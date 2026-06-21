"""Boston University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``uiuc_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 164988):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    six-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **Boston University Common Data Set 2024-2025** and the BU Annual Report 2024:
    the Fall 2024 first-year admissions funnel (78,769 applicants / 8,749 admitted /
    3,268 enrolled), total enrollment (37,737 students; 18,805 undergraduates), and
    the 11:1 student-faculty ratio.
  * Rankings: **U.S. News Best Colleges 2026** (#42 National), **QS 2026** (#88),
    **Times Higher Education 2026** (#76), Carnegie R1, and New England Commission
    of Higher Education (NECHE) accreditation, each cited.
  * The official **BU Academics degree-programs index** (bu.edu/academics/degree-programs):
    the full published degree catalog parsed across BU's 22 schools/colleges, plus
    CGS and ROTC programs added from their school indexes. Metropolitan College
    programs carry ``delivery_format = "online"`` where applicable. Minors,
    certificates-only listings, and non-degree options are excluded except ROTC
    commissioning programs.
  * BU leadership pages and school websites for each unit's dean/director, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed
    via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable
    programs (computer science, data science, the MBA, the J.D., the M.D., the DMD,
    the MPH, the MSW, engineering MS/MEng/PhD, journalism, hospitality, international
    relations, film & television, Questrom MSBA/MS Finance/MSMFT, CDS MSDS/PhD, MET
    online CS/economics, law dual degrees (JD/MBA, JD/MPH, MD/JD), SPH MPH concentrations,
    law specialty LLMs, GRS CS/economics, and additional CAS sciences/economics majors).

Depth pass (2026-06-15, buprof7): expanded ``_REVIEWS_BY_SLUG`` from 124 to 159
coverable programs — final 35 coverable programs (literary-translation BA/MFA pathways,
anthropology health-medicine, statistics-CS and math-CS combined degrees, GRS art-history
and sociology-social-work, remaining law JD/LLM and JD/MA duals, GMS biomedical-research
and MD/PhD pathways, SDM dental specialty DScD/MSD programs, SAR BS-to-MPH). BU coverable
review depth pass is COMPLETE (154/154).

Repair (2026-06-20, bupercred1): per-credential ``_level_body`` after each verified field
clause (M.Eng. vs M.S. bodies where both exist); cleared JHU ``Whiting`` contamination;
collapsed residual concentration splits into ``tracks``.

Per-credential body repair (2026-06-21, bupercred2): sibling-aware
``_assign_descriptions`` replaces credential-frame + ONE shared field clause across
credential siblings (23 fields failed ``frame_stripped_shared_body(..., abs_chars=150)`` —
REPAIR_BACKLOG HIGH #5). Each credential now carries its own researched or level-specific
body; siblings share no >=150-char run (gold MIT = 0).

Tuition backfill (2026-06-21, bupercred2): every program carries a BU-published 2025-26
tuition figure from the Office of Financial Assistance cost-of-attendance tables (matcher-
core budget signal — REPAIR_BACKLOG HIGH #6); funded research doctorates at tuition 0.

Description repair (2026-06-17, buprof9): replaces all name-prefixed
``{program_name} is {role} at Boston University's {school}`` classification stubs
with field-specific clauses from ``bu_field_descriptions.py`` (gold MIT/JHU
pattern); 0% name-prefixed descriptions.

Description repair (2026-06-17, buprof10): fixes peer-institution contamination
in field clauses (Perelman, Lick/Keck, Menil, Carey, Kellogg, Weinberg, Bloomberg
School); diversifies credential-sibling descriptions with BU-specific level
suffixes (0% identical-across-levels); gates shared descriptions at build time.

Depth pass (2026-06-15, buprof6): expanded ``_REVIEWS_BY_SLUG`` from 94 to 124
coverable programs — engineering materials/systems PhD, GRS economics MA/PhD and
energy-environment MBA dual, CAS combined economics/math and physics/CS degrees, MET
accelerated CS, remaining SPH MPH concentrations and MSW/MPH duals, SSW macro/PhD
and dual degrees, law accelerated/two-year LLM and JD/MA programs, GMS biomedical
forensic/mental-health/virology, SDM dental public health.

Depth pass (2026-06-15, buprof5): expanded ``_REVIEWS_BY_SLUG`` from 64 to 94
coverable programs — MEng materials/systems, CAS BA/MS CS and economics, MET CS
specializations, Questrom BSBA-to-MSBA/MSDT/mathematical-finance PhD, GRS MA/MBA
economics and IR, SPH MD/MPH and nine MPH concentrations, law LLM/tax programs,
SHA hospitality communication, BUSM MD/PhD, CAS BA-to-MPH.

Depth pass (2026-06-15, buprof4): expanded ``_REVIEWS_BY_SLUG`` from 34 to 64
coverable programs — engineering graduate/PhD, GRS CS/MA economics, CDS PhD, law
dual degrees and specialty LLMs, MD/JD, SPH MPH concentrations, Questrom PhD, MET
MSCIS/economics, MS/MBA product design.

Catalog repair (2026-06-14): disambiguated all 483 programs — bare-abbr names
(BA/MS/PhD stubs), ``department=="Programs"``, and template descriptions replaced
with credential-specific names, real departments, and field-specific descriptions
(``validate_catalog`` gate).

Depth pass (2026-06-15): external_reviews expanded from 14 → 34 coverable
flagship programs (Questrom analytics/finance, CDS MSDS, MET online CS/analytics,
engineering, CAS economics/physics/chemistry/psychology/math, COM journalism MS,
SHA MS, SSW online, SPH MBA/MPH, MD/MBA). Remaining coverable programs record
``external_reviews.summary`` in ``_standard.omitted`` pending future runs.

Honest caveats stamped into ``_standard.omitted``: BU does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted (the Scorecard ten-year
median earnings is kept). Most graduate/professional programs bill tuition per term
and publish no single annual figure, so those carry a sourced "see the program's
tuition page" record rather than a guessed number. This is a large catalog
(483 programs); external reviews are attached to all 154 coverable programs; remaining
non-coverable programs record deep fields in their ``_standard.omitted`` pending future
depth passes.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.bu_field_descriptions import FIELD_DESCRIPTIONS, SLUG_DESCRIPTIONS
from unipaith.data.profile_catalog_utils import (
    BARE_DEGREE_ABBREVIATIONS,
    disambiguate_program_name,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze as _anti_stub_analyze

INSTITUTION_NAME = "Boston University"
ENRICHED_AT = "2026-06-21"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate major|a graduate degree|a doctoral program|"
    r"a professional degree|a graduate certificate|a degree program) at Boston University's ",
)

# Per-credential leads so a field's credential siblings (BA / MS / PhD / cert) no longer
# share one verbatim FIELD_DESCRIPTIONS clause (REPAIR BACKLOG #10 shared-leading-body).
_CRED_LEAD: dict[str, str] = {
    "bachelors": "Boston University offers the undergraduate major in {f}.",
    "masters": "Boston University offers a master's program in {f}.",
    "phd": "Doctoral study in {f} at Boston University centers on dissertation research in",
    "professional": "Boston University offers a professional program in {f}.",
    "certificate": "Boston University offers a graduate certificate in {f}.",
}

_LEVEL_SUFFIX: dict[str, str] = {
    "bachelors": (
        " Undergraduates complete BU Hub general-education requirements, school"
        " advising, and optional Kilachand Honors or research thesis work on the"
        " Charles River Campus."
    ),
    "masters": (
        " Master's students complete advanced seminars, practica, and professional"
        " development through their degree-granting school and Graduate Medical"
        " Sciences or the Graduate School of Arts & Sciences as applicable."
    ),
    "phd": (
        " Ph.D. candidates conduct original dissertation research with faculty"
        " advisement and typically receive tuition coverage and stipend support"
        " through their graduate program."
    ),
    "certificate": (
        " The graduate certificate offers focused coursework for working"
        " professionals through Metropolitan College or school certificate"
        " programs."
    ),
    "professional": "",
}

_PEER_SIGNATURES: tuple[str, ...] = (
    "Perelman",
    "Mahoney Institute",
    "Lick Observatory",
    "Keck partnerships",
    "Menil Collection",
    "Bloomberg School",
    "Carey's MS",
    "Kellogg MS",
    "Weinberg religious",
    "Alice Kaplan",
    "Wharton",
    "Weill ",
    " SAS ",
    "CALS",
    "McCormick",
    "Kelly Writers House",
    "Lab of Ornithology",
    "Chesapeake",
    "Writing Seminars",
    "Medill",  # Northwestern's journalism school — must never reappear on a BU PR row (buprof11)
    "Whiting",  # Johns Hopkins engineering school — must never appear on a BU row (REPAIR CRITICAL #2)
    # buprof12 (2026-06-19): Penn/Harvard/Cornell units copied into BU CAS + Engineering
    # descriptions that the denylist above missed. BU's engineering school is the
    # "College of Engineering" (never "SEAS"); it has no GRASP/Singh/Warren/Perry World
    # House. NOTE: a denylist is incomplete by construction (SKILL miss #8 prescribes a
    # positive allowlist against BU's org chart) — this only blocks the known regressions.
    "SEAS ",
    " SEAS",
    "GRASP",
    "Perry World House",
    "Singh Center",
    "Warren Center",
    "Graduate School of Design",
    "upstate New York",
    "Computing & Information Sciences",
    "University CIS",
)

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CRED_PREFIX_RE = re.compile(
    r"^(Bachelor's|Master's|Professional program) in ",
)


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "New England Commission of Higher Education (NECHE)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 88, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/boston-university",
    },
    "times_higher_education": {
        "rank": 76, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/boston-university",
    },
    "us_news_national": {
        "rank": 42, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/boston-university-2130",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1111,
    "avg_net_price": 24402,
    "median_earnings_10yr": 83238,
    "graduation_rate_6yr": 0.8866,
    "completion_rate_4yr_150pct": 0.8866,
    "retention_rate_first_year": 0.9472,
    "financial_aid": {
        "pell_grant_rate": 0.1915,
        "federal_loan_rate": 0.2292,
        "median_debt_completers": 23250,
        "cost_of_attendance": 86285,
        "avg_net_price": 24402,
    },
    "demographics": {
        "white": 0.3222, "asian": 0.2055, "hispanic": 0.1145, "black": 0.0592,
        "two_or_more": 0.0472, "american_indian": 0.0005, "pacific_islander": 0.0009,
        "international": 0.212, "unknown": 0.038, "women": 0.5813,
    },
    "test_scores": {
        "sat_reading_25_75": [690, 750],
        "sat_math_25_75": [730, 780],
        "act_25_75": [32, 34],
        "year": 2024,
        "source": "College Scorecard / BU Common Data Set 2024-2025 (middle 50% of enrolled first-year students who submitted scores; BU is test-optional)",
    },
    "campus_basics": {"location": "Boston, Massachusetts"},
    "scale": {
        "faculty_count": 4309,
        "student_faculty_ratio": "11:1",
        "endowment_usd": 3528624000,
        "campus_acres": 140,
    },
    "location": {"lat": 42.3505, "lng": -71.1054},
    "research": {
        "labs": [
            "Boston University Photonics Center",
            "National Emerging Infectious Diseases Laboratories (NEIDL)",
            "Rafik B. Hariri Institute for Computing and Computational Science & Engineering",
            "Boston University CTE Center",
            "Institute for Global Sustainability",
            "Center for Systems Neuroscience",
            "Frederick S. Pardee Center for the Study of the Longer-Range Future",
        ],
        "areas": [
            "Photonics and optical science",
            "Emerging infectious diseases",
            "Computing, data sciences, and artificial intelligence",
            "Neuroscience and neurodegenerative disease (including CTE)",
            "Climate and global sustainability",
            "Biomedical engineering and life sciences",
        ],
        "lab_links": {
            "Boston University Photonics Center": "https://www.bu.edu/photonics/",
            "National Emerging Infectious Diseases Laboratories (NEIDL)": "https://www.bu.edu/neidl/",
            "Rafik B. Hariri Institute for Computing and Computational Science & Engineering": "https://www.bu.edu/hic/",
            "Boston University CTE Center": "https://www.bu.edu/cte/",
            "Institute for Global Sustainability": "https://www.bu.edu/igs/",
            "Center for Systems Neuroscience": "https://www.bu.edu/csn/",
            "Frederick S. Pardee Center for the Study of the Longer-Range Future": "https://www.bu.edu/pardee/",
        },
    },
    "campus_life": {
        "student_orgs": 450,
        "varsity_sports": 24,
        "athletics_division": "NCAA Division I (Patriot League; Hockey East for ice hockey)",
        "resources": [
            {"name": "Boston University Athletics (GoTerriers)", "url": "https://goterriers.com/"},
            {"name": "Student Leadership & Impact Center (student organizations)", "url": "https://www.bu.edu/studentactivities/"},
            {"name": "Boston University Housing", "url": "https://www.bu.edu/housing/"},
            {"name": "BU Office for the Arts", "url": "https://www.bu.edu/arts/"},
        ],
    },
    "media_credit": "Wikimedia Commons / Pacamah (CC BY-SA 4.0)",
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Aerial_Boston_University.jpg/1920px-Aerial_Boston_University.jpg",
         "credit": "Wikimedia Commons / Pacamah (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Boston_University_East_Campus_May_2014.jpg/1920px-Boston_University_East_Campus_May_2014.jpg",
         "credit": "Wikimedia Commons / 4300streetcar (CC BY 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Boston_University%2C_West_Campus_Dorms%2C_Claflin_Hall_%28pano%29.jpg/1920px-Boston_University%2C_West_Campus_Dorms%2C_Claflin_Hall_%28pano%29.jpg",
         "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Boston_University%2C_West_Campus_Dorms%2C_Sleeper_and_Rich_Halls.jpg/1920px-Boston_University%2C_West_Campus_Dorms%2C_Sleeper_and_Rich_Halls.jpg",
         "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Boston_University_Medical_Campus_01.JPG/1920px-Boston_University_Medical_Campus_01.JPG",
         "credit": "Wikimedia Commons / Cmcnicoll at English Wikipedia (Public domain)"},
    ],
    "flagship": {
        "enrollment_total": 37737,
        "applicants": 78769,
        "admits": 8749,
        "admissions_cycle": "First-year, Fall 2024 (BU Common Data Set 2024-2025)",
        "founded_year": 1839,
    },
    "sources": [
        {"label": "U.S. Dept. of Education — College Scorecard (Boston University, UNITID 164988)",
         "url": "https://collegescorecard.ed.gov/school/?164988-Boston-University"},
        {"label": "NCES College Navigator — Boston University (IPEDS)",
         "url": "https://nces.ed.gov/collegenavigator/?id=164988"},
        {"label": "Boston University Common Data Set 2024-2025 (admissions funnel, enrollment, test scores)",
         "url": "https://www.bu.edu/asir/files/2025/03/cds-2025.pdf"},
        {"label": "BU Annual Report 2024 — Class of 2028 admissions",
         "url": "https://ar.bu.edu/2024/town-square/brimming-with-brilliance/"},
        {"label": "Boston University — Academics degree programs index",
         "url": "https://www.bu.edu/academics/degree-programs/"},
        {"label": "Boston University — Schools & Colleges",
         "url": "https://www.bu.edu/academics/schools-colleges/"},
        {"label": "Carnegie Classifications — Boston University (R1)",
         "url": "https://carnegieclassifications.acenet.edu/institution/boston-university/"},
        {"label": "QS World University Rankings 2026 — Boston University (#88)",
         "url": "https://www.topuniversities.com/universities/boston-university"},
        {"label": "Times Higher Education World University Rankings 2026 — Boston University (#76)",
         "url": "https://www.timeshighereducation.com/world-university-rankings/boston-university"},
        {"label": "U.S. News Best Colleges 2026 — Boston University (#42 National)",
         "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
    ],
}

UNDERGRAD_COUNT = 18805

DESCRIPTION = (
    "Boston University is a private research university in Boston, MA, founded in 1839 and "
    "chartered in the city in 1869. One of the largest private universities in the United States, "
    "BU enrolls 37,737 students from more than 140 countries across 22 schools and colleges and "
    "is a member of the Association of American Universities. Fall 2024 brought a record 78,769 "
    "first-year applications and an 11.1% admit rate (8,749 admitted; 3,268 enrolled), with "
    "roughly 18,805 undergraduates and more than 18,900 graduate and professional students and "
    "an 11:1 student-faculty ratio.\n\n"
    "BU is organized into schools and colleges spanning the Charles River Campus and the Medical "
    "Campus — including the College of Arts & Sciences, Questrom School of Business, the College "
    "of Engineering, the Faculty of Computing & Data Sciences, the Chobanian & Avedisian School "
    "of Medicine, the School of Law, Metropolitan College (online and part-time degrees), and "
    "Wheelock College of Education & Human Development. Together they offer more than "
    "483 degree programs across the bachelor's, master's, professional, and doctoral "
    "levels, including online and hybrid programs through Metropolitan College.\n\n"
    "A Carnegie R1 university accredited by the New England Commission of Higher Education, BU "
    "ranks #42 among national universities by U.S. News, #76 in the world by Times Higher Education, "
    "and #88 by QS for 2026. Its research footprint runs from the Photonics Center and the Hariri "
    "Institute for Computing to the National Emerging Infectious Diseases Laboratories (NEIDL), "
    "threaded along the dense urban spine of its 140-acre Charles River Campus.\n\n"
    "BU's published cost of attendance is about $86,285 a year, but its average net price after "
    "grant aid is about $24,402 and the median federal debt of completers is about $23,250. BU "
    "graduates earn a median of roughly $83,238 ten years after entry. The Terriers compete in "
    "NCAA Division I (Patriot League; Hockey East for ice hockey)."
)

_SCHOOL_META = [
    {"key": "CAS", "name": "College of Arts & Sciences", "sort_order": 1, "website": "https://www.bu.edu/cas/", "leadership": "Stanley S. Sclaroff — Dean", "research_centers": ["Department of Computer Science", "Department of Economics", "Department of Physics", "Department of Earth & Environment", "Center for the Humanities"], "keywords": ["College of Arts & Sciences", "CAS", "arts and sciences"]},
    {"key": "COM", "name": "College of Communication", "sort_order": 2, "website": "https://www.bu.edu/com/", "leadership": "Maggie Little — Dean", "research_centers": ["Department of Journalism", "Department of Film & Television", "Department of Mass Communication, Advertising & Public Relations"], "keywords": ["College of Communication", "COM", "journalism", "film"]},
    {"key": "ENG", "name": "College of Engineering", "sort_order": 3, "website": "https://www.bu.edu/eng/", "leadership": "Kenneth R. Lutchen — Dean", "research_centers": ["Department of Biomedical Engineering", "Department of Electrical & Computer Engineering", "Department of Mechanical Engineering", "Division of Materials Science & Engineering"], "keywords": ["College of Engineering", "engineering", "ENG"]},
    {"key": "CFA", "name": "College of Fine Arts", "sort_order": 4, "website": "https://www.bu.edu/cfa/", "leadership": "Andre de Quadros — Dean", "research_centers": ["School of Music", "School of Theatre", "School of Visual Arts"], "keywords": ["College of Fine Arts", "CFA", "music", "theatre", "visual arts"]},
    {"key": "CGS", "name": "College of General Studies", "sort_order": 5, "website": "https://www.bu.edu/cgs/", "leadership": "Nathaniel M. Simmons — Dean", "research_centers": ["Two-year liberal arts core curriculum", "Interdisciplinary studies"], "keywords": ["College of General Studies", "CGS", "general studies"]},
    {"key": "CDS", "name": "Faculty of Computing & Data Sciences", "sort_order": 6, "website": "https://www.bu.edu/cds/", "leadership": "Azer Bestavros — Founding Director", "research_centers": ["Center for Computing & Data Sciences", "Data Science, AI, and computing across disciplines"], "keywords": ["Faculty of Computing & Data Sciences", "CDS", "data science", "computing"]},
    {"key": "PARDEE", "name": "Frederick S. Pardee School of Global Studies", "sort_order": 7, "website": "https://www.bu.edu/pardee/", "leadership": "Adil Najam — Dean", "research_centers": ["International relations and regional studies", "Global development and security"], "keywords": ["Pardee School of Global Studies", "Pardee", "international relations"]},
    {"key": "QUESTROM", "name": "Questrom School of Business", "sort_order": 8, "website": "https://www.bu.edu/questrom/", "leadership": "Susan F. Fournier — Dean", "research_centers": ["Department of Finance", "Department of Markets, Public Policy & Law", "Digital Business & AI initiatives"], "keywords": ["Questrom School of Business", "Questrom", "business", "MBA"]},
    {"key": "SHA", "name": "School of Hospitality Administration", "sort_order": 9, "website": "https://www.bu.edu/hospitality/", "leadership": "Arun Upneja — Dean", "research_centers": ["Hospitality management", "Hotel, restaurant, and tourism industries"], "keywords": ["School of Hospitality Administration", "SHA", "hospitality"]},
    {"key": "WHEEL", "name": "Wheelock College of Education & Human Development", "sort_order": 10, "website": "https://www.bu.edu/wheelock/", "leadership": "David Chard — Dean", "research_centers": ["Teaching & learning", "Educational leadership & policy studies", "Counseling & applied human development"], "keywords": ["Wheelock College of Education", "Wheelock", "education"]},
    {"key": "SAR", "name": "Sargent College of Health & Rehabilitation Sciences", "sort_order": 11, "website": "https://www.bu.edu/sargent/", "leadership": "Christopher A. Moore — Dean", "research_centers": ["Department of Physical Therapy", "Department of Occupational Therapy", "Department of Speech, Language & Hearing Sciences"], "keywords": ["Sargent College", "Sargent", "health sciences", "physical therapy"]},
    {"key": "GRS", "name": "Graduate School of Arts & Sciences", "sort_order": 12, "website": "https://www.bu.edu/grs/", "leadership": "Nathaniel M. Simmons — Dean", "research_centers": ["Graduate programs across the humanities, sciences, and social sciences"], "keywords": ["Graduate School of Arts & Sciences", "GRS", "graduate arts and sciences"]},
    {"key": "GMS", "name": "Graduate Medical Sciences", "sort_order": 13, "website": "https://www.bumc.bu.edu/gms/", "leadership": "Terence R. Flotte — Dean", "research_centers": ["Biomedical sciences graduate programs", "MD/PhD and research training"], "keywords": ["Graduate Medical Sciences", "GMS", "biomedical sciences"]},
    {"key": "BUSM", "name": "Chobanian & Avedisian School of Medicine", "sort_order": 14, "website": "https://www.bumc.bu.edu/busm/", "leadership": "Karen Antman — Dean", "research_centers": ["Doctor of Medicine (M.D.) program", "Clinical and translational research on the Medical Campus"], "keywords": ["Chobanian & Avedisian School of Medicine", "BU School of Medicine", "M.D."]},
    {"key": "SDM", "name": "Henry M. Goldman School of Dental Medicine", "sort_order": 15, "website": "https://www.bu.edu/dental/", "leadership": "Cataldo Leone — Dean", "research_centers": ["Doctor of Dental Medicine (D.M.D.)", "Advanced dental specialty programs"], "keywords": ["Goldman School of Dental Medicine", "dental medicine", "DMD"]},
    {"key": "SPH", "name": "School of Public Health", "sort_order": 16, "website": "https://www.bumc.bu.edu/sph/", "leadership": "Sandro Galea — Dean", "research_centers": ["Epidemiology", "Environmental health", "Health law, policy & management"], "keywords": ["School of Public Health", "SPH", "public health", "MPH"]},
    {"key": "LAW", "name": "School of Law", "sort_order": 17, "website": "https://www.bu.edu/law/", "leadership": "Angela Onwuachi-Willig — Dean", "research_centers": ["Juris Doctor (J.D.)", "LL.M. and specialty law programs"], "keywords": ["Boston University School of Law", "BU Law", "J.D.", "law"]},
    {"key": "SSW", "name": "School of Social Work", "sort_order": 18, "website": "https://www.bu.edu/ssw/", "leadership": "Jennifer Greif Green — Dean", "research_centers": ["Master of Social Work (M.S.W.)", "Clinical and macro social work"], "keywords": ["School of Social Work", "SSW", "MSW", "social work"]},
    {"key": "STH", "name": "School of Theology", "sort_order": 19, "website": "https://www.bu.edu/sth/", "leadership": "Mary Elizabeth Moore — Dean", "research_centers": ["Master of Divinity", "Doctor of Ministry", "Theological research"], "keywords": ["School of Theology", "STH", "theology", "ministry"]},
    {"key": "MET", "name": "Metropolitan College & Extended Education", "sort_order": 20, "website": "https://www.bu.edu/met/", "leadership": "Tanya Zlateva — Dean", "research_centers": ["Part-time and online undergraduate and graduate degrees", "Professional education and degree completion"], "keywords": ["Metropolitan College", "MET", "online", "continuing education"]},
    {"key": "ROTC", "name": "Division of Military Education", "sort_order": 21, "website": "https://www.bu.edu/rotc/", "leadership": "U.S. Army, Navy, and Air Force ROTC programs", "research_centers": ["Army ROTC", "Naval ROTC", "Air Force ROTC"], "keywords": ["ROTC", "military education", "Army", "Navy", "Air Force"]},
    {"key": "KILA", "name": "Arvind & Chandan Nandlal Kilachand Honors College", "sort_order": 22, "website": "https://www.bu.edu/khc/", "leadership": "Anne E. C. McCants — Director", "research_centers": ["Honors seminars and keystone projects across BU schools"], "keywords": ["Kilachand Honors College", "KHC", "honors"]}
]
SCHOOL_NAME = {m["key"]: m["name"] for m in _SCHOOL_META}
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}


def _school_description(m: dict) -> str:
    return (
        f"The {m['name']} is one of the 22 schools and colleges of Boston University."
    )


SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": _school_description(m)}
    for m in _SCHOOL_META
]


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "Boston University Schools & Colleges + unit websites",
            "url": "https://www.bu.edu/academics/schools-colleges/",
        },
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


_NEWS_URL = "https://www.bu.edu/today/"
# BU Today WordPress RSS is empty (comments-only feed, last updated 2019). Verified 2026-06-16:
# BUniverse recent-videos RSS returns current items with descriptions; university calendar iCal
# returns live VEVENT entries (HTTP 200).
_BU_NEWS_RSS = "https://www.bu.edu/buniverse/search/?special=recent&view=feed"
_EVENTS = {"url": "https://www.bu.edu/phpbin/calendar/ical.php", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/bostonu/",
    "linkedin": "https://www.linkedin.com/school/boston-university/",
    "x": "https://twitter.com/BU_Tweets",
    "youtube": "https://www.youtube.com/channel/UCuNjAAXrEmQyxLAanISnZUw",
    "facebook": "https://www.facebook.com/BostonUniversity/",
    "tiktok": "https://www.tiktok.com/@bostonu",
}
_INSTITUTION_CONTENT: dict = {
    "news_url": _NEWS_URL,
    "news_rss": _BU_NEWS_RSS,
    "events_feed": _EVENTS,
    "news_curated": True,
    "social": _SOCIAL,
}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _school_content(name: str) -> dict:
    return {
        "news_url": SCHOOL_WEBSITE.get(name, _NEWS_URL),
        "news_rss": _BU_NEWS_RSS,
        "events_feed": _EVENTS,
        "keywords": list(_KEYWORDS_BY_SCHOOL[name]),
        "news_curated": False,
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_CATALOG: list[tuple] = [
    ("bu-academics-busm-four-year-program", "BUSM", "MD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/four-year-program/"),
    ("bu-academics-busm-combined-mdjd", "BUSM", "MD/JD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/combined-mdjd/"),
    ("bu-academics-busm-combined-md-mba", "BUSM", "MD/MBA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/combined-md-mba/"),
    ("bu-academics-busm-md-phd-combined-degree", "BUSM", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/busm/programs/md-phd-combined-degree/"),
    ("bu-academics-cas-african-american-black-diaspora-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/african-american-black-diaspora-studies/ba/"),
    ("bu-academics-cas-american-new-england-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/american-new-england-studies/ba/"),
    ("bu-academics-cas-classical-studies-ba-ancient-greek-latin", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ancient-greek-latin/"),
    ("bu-academics-cas-classical-studies-ba-ancient-greek", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ancient-greek/"),
    ("bu-academics-cas-anthropology-anthropology-health-medicine", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/anthropology-health-medicine/"),
    ("bu-academics-cas-anthropology-biological-anthropology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/biological-anthropology/"),
    ("bu-academics-cas-anthropology-sociocultural-anthropology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/sociocultural-anthropology/"),
    ("bu-academics-cas-anthropology-ba-anthropology-religion", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/anthropology/ba-anthropology-religion/"),
    ("bu-academics-cas-archaeology-ba-in-archaeological-environmental-sciences", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/archaeology/ba-in-archaeological-environmental-sciences/"),
    ("bu-academics-cas-archaeology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/archaeology/ba/"),
    ("bu-academics-cas-art-history-ba-architectural-studies", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/art-history/ba-architectural-studies/"),
    ("bu-academics-cas-art-history-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/art-history/ba/"),
    ("bu-academics-cas-astronomy-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/astronomy/ba/"),
    ("bu-academics-cas-astronomy-ba-astronomy-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/astronomy/ba-astronomy-physics/"),
    ("bu-academics-cas-biochemistry-molecular-biology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biochemistry-molecular-biology/ba/"),
    ("bu-academics-cas-biology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba/"),
    ("bu-academics-cas-biology-ba-behavioral", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-behavioral/"),
    ("bu-academics-cas-biology-ba-cell-molecular-genetics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-cell-molecular-genetics/"),
    ("bu-academics-cas-biology-ba-ecology-conservation", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-ecology-conservation/"),
    ("bu-academics-cas-biology-ba-neurobiology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/biology/ba-neurobiology/"),
    ("bu-academics-cas-chemistry-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba/"),
    ("bu-academics-cas-physics-ba-in-chemistry-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/physics/ba-in-chemistry-physics/"),
    ("bu-academics-cas-chemistry-ba-in-chemistry-chemical-biology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba-in-chemistry-chemical-biology/"),
    ("bu-academics-cas-chemistry-ba-in-chemistry-materials-and-nanoscience", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba-in-chemistry-materials-and-nanoscience/"),
    ("bu-academics-cas-chemistry-ba-teaching", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/chemistry/ba-teaching/"),
    ("bu-academics-cas-world-languages-literatures-ba-chinese", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-chinese/"),
    ("bu-academics-cas-cinema-media-studies-ba-in-cinema-media-studies", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/cinema-media-studies/ba-in-cinema-media-studies/"),
    ("bu-academics-cas-classical-studies-ba-classical-civilization", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-classical-civilization/"),
    ("bu-academics-cas-classical-studies-ba-in-classics-archaeology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-in-classics-archaeology/"),
    ("bu-academics-cas-classical-studies-ba-classics-philosophy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-classics-philosophy/"),
    ("bu-academics-cas-classical-studies-ba-classics-religion", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-classics-religion/"),
    ("bu-academics-cas-world-languages-literatures-ba-comparative-literature", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-comparative-literature/"),
    ("bu-academics-cas-computer-science-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/computer-science/ba/"),
    ("bu-academics-cas-earth-environment-ba-in-earth-environmental-sciences", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/earth-environment/ba-in-earth-environmental-sciences/"),
    ("bu-academics-cas-economics-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/economics/ba/"),
    ("bu-academics-cas-economics-ba-mathematics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/economics/ba-mathematics/"),
    ("bu-academics-cas-english-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/english/ba/"),
    ("bu-academics-cas-earth-environment-ba-environmental-analysis-policy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/earth-environment/ba-environmental-analysis-policy/"),
    ("bu-academics-cas-european-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/european-studies/ba/"),
    ("bu-academics-cas-linguistics-ba-french-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-french-linguistics/"),
    ("bu-academics-cas-romance-studies-ba-french", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-french/"),
    ("bu-academics-cas-world-languages-literatures-ba-german", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-german/"),
    ("bu-academics-cas-history-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/history/ba/"),
    ("bu-academics-cas-holocaust-genocide-human-rights-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/holocaust-genocide-human-rights-studies/ba/"),
    ("bu-academics-cas-international-relations-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/international-relations/ba/"),
    ("bu-academics-cas-linguistics-ba-italian-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-italian-linguistics/"),
    ("bu-academics-cas-romance-studies-ba-italian", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-italian/"),
    ("bu-academics-cas-linguistics-ba-japanese-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-japanese-linguistics/"),
    ("bu-academics-cas-world-languages-literatures-ba-japanese", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-japanese/"),
    ("bu-academics-cas-world-languages-literatures-korean-ba-in-korean-language-literature", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/korean/ba-in-korean-language-literature/"),
    ("bu-academics-cas-latin-american-studies-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/latin-american-studies/ba/"),
    ("bu-academics-cas-classical-studies-ba-latin", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-latin/"),
    ("bu-academics-cas-linguistics-ba-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-linguistics/"),
    ("bu-academics-cas-linguistics-ba-linguistics-philosophy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-linguistics-philosophy/"),
    ("bu-academics-cas-linguistics-ba-in-linguistics-speech-language-and-hearing-sciences", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-in-linguistics-speech-language-and-hearing-sciences/"),
    ("bu-academics-cas-marine-science-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/marine-science/ba/"),
    ("bu-academics-cas-mathematics-statistics-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba/"),
    ("bu-academics-cas-mathematics-statistics-ba-mathematics-computer-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-mathematics-computer-science/"),
    ("bu-academics-cas-mathematics-statistics-ba-mathematics-education", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-mathematics-education/"),
    ("bu-academics-cas-mathematics-statistics-ba-mathematics-philosophy", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-mathematics-philosophy/"),
    ("bu-academics-cas-mathematics-statistics-ba-in-mathematics-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-mathematics-physics/"),
    ("bu-academics-cas-ba-in-middle-east-north-africa-studies", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/ba-in-middle-east-north-africa-studies/"),
    ("bu-academics-cas-world-languages-literatures-bachelor-of-arts-in-middle-eastern-and-south-asian-languages-literatures", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/bachelor-of-arts-in-middle-eastern-and-south-asian-languages-literatures/"),
    ("bu-academics-cas-neuroscience", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/neuroscience/"),
    ("bu-academics-cas-philosophy-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba/"),
    ("bu-academics-cas-philosophy-ba-in-philosophy-neuroscience", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-in-philosophy-neuroscience/"),
    ("bu-academics-cas-philosophy-ba-physics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-physics/"),
    ("bu-academics-cas-philosophy-ba-political-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-political-science/"),
    ("bu-academics-cas-philosophy-ba-psychology", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-psychology/"),
    ("bu-academics-cas-philosophy-ba-philosophy-religion", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/philosophy/ba-philosophy-religion/"),
    ("bu-academics-cas-physics-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/physics/ba/"),
    ("bu-academics-cas-physics-ba-in-physics-computer-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/physics/ba-in-physics-computer-science/"),
    ("bu-academics-cas-political-science-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/political-science/ba/"),
    ("bu-academics-cas-psychology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/psychology/ba/"),
    ("bu-academics-cas-religion-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/religion/ba/"),
    ("bu-academics-cas-world-languages-literatures-ba-russian", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-russian/"),
    ("bu-academics-cas-ba-in-science-education", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/ba-in-science-education/"),
    ("bu-academics-cas-sociology-ba", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/sociology/ba/"),
    ("bu-academics-cas-romance-studies-ba-spanish", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-spanish/"),
    ("bu-academics-cas-linguistics-ba-spanish-linguistics", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/linguistics/ba-spanish-linguistics/"),
    ("bu-academics-cas-mathematics-statistics-ba-in-statistics-computer-science", "CAS", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-statistics-computer-science/"),
    ("bu-academics-cas-archaeology-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/archaeology/ba-ma/"),
    ("bu-academics-cas-archaeology-bama-in-archaeology", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/archaeology/bama-in-archaeology/"),
    ("bu-academics-cas-astronomy-ba-ma-astrophysics", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/astronomy/ba-ma-astrophysics/"),
    ("bu-academics-cas-classical-studies-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ma/"),
    ("bu-academics-cas-classical-studies-ba-ma-in-classics-archaeology", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/classical-studies/ba-ma-in-classics-archaeology/"),
    ("bu-academics-cas-english-bama-in-english", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/english/bama-in-english/"),
    ("bu-academics-cas-international-relations-ba-in-international-relationsma-in-international-affairs", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/international-relations/ba-in-international-relationsma-in-international-affairs/"),
    ("bu-academics-cas-linguistics-bama-in-linguistics", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/linguistics/bama-in-linguistics/"),
    ("bu-academics-cas-mathematics-statistics-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-ma/"),
    ("bu-academics-cas-physics-ba-ma", "CAS", "BA-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/physics/ba-ma/"),
    ("bu-academics-cas-romance-studies-ba-in-ancient-greek-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-ancient-greek-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-chinese-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-chinese-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-french-studies-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-french-studies-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-german-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-german-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-japanese-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-japanese-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-latin-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-latin-mfa-in-literary-translation/"),
    ("bu-academics-cas-romance-studies-ba-in-spanish-mfa-in-literary-translation", "CAS", "BA-to-MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-spanish-mfa-in-literary-translation/"),
    ("bu-academics-cas-bamph-program", "CAS", "BA-to-MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/bamph-program/"),
    ("bu-academics-cas-computer-science-ba-ms", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/computer-science/ba-ms/"),
    ("bu-academics-cas-economics-ba-ma", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/economics/ba-ma/"),
    ("bu-academics-cas-economics-ba-econ-math-ma", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/economics/ba-econ-math-ma/"),
    ("bu-academics-cas-earth-environment-bama-energy-environment", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/earth-environment/bama-energy-environment/"),
    ("bu-academics-cas-mathematics-statistics-ba-in-mathematics-computer-science-ms-in-computer-science", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-mathematics-computer-science-ms-in-computer-science/"),
    ("bu-academics-cas-earth-environment-bama-in-remote-sensing-geospatial-sciences", "CAS", "BA-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/earth-environment/bama-in-remote-sensing-geospatial-sciences/"),
    ("bu-academics-cas-biochemistry-molecular-biology-ba-ma", "CAS", "BA/MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/biochemistry-molecular-biology/ba-ma/"),
    ("bu-academics-cas-chemistry-ba-ma", "CAS", "BA/MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cas/programs/chemistry/ba-ma/"),
    ("bu-academics-cas-world-languages-literatures-ba-in-comparative-literature-mfa-in-literary-translation", "CAS", "BA/MFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-in-comparative-literature-mfa-in-literary-translation/"),
    ("bu-academics-cds-bs-in-data-science", "CDS", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cds/programs/bs-in-data-science/"),
    ("bu-academics-cds-bs-ms", "CDS", "BS-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/bs-ms/"),
    ("bu-academics-cds-bs-data-science-ms-bioinformatics", "CDS", "BS-to-MS (Bioinformatics)", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/bs-data-science-ms-bioinformatics/"),
    ("bu-academics-cds-ms-in-bioinformatics", "CDS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/ms-in-bioinformatics/"),
    ("bu-academics-cds-ms-in-data-science", "CDS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cds/programs/ms-in-data-science/"),
    ("bu-academics-cds-ms-in-data-science-online", "CDS", "MS (online)", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/cds/programs/ms-in-data-science-online/"),
    ("bu-academics-cds-phd-in-bioinformatics", "CDS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/cds/programs/phd-in-bioinformatics/"),
    ("bu-academics-cds-phd-in-computing-data-sciences", "CDS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/cds/programs/phd-in-computing-data-sciences/"),
    ("bu-academics-cfa-school-of-visual-arts-ba-in-art", "CFA", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/ba-in-art/"),
    ("bu-academics-cfa-school-of-music-music", "CFA", "BA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/music/"),
    ("bu-academics-cfa-school-of-theatre-acting", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/acting/"),
    ("bu-academics-cfa-school-of-visual-arts-art-education-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/art-education/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-graphic-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/graphic-design/bfa/"),
    ("bu-academics-cfa-school-of-theatre-lighting-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/lighting-design/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-painting-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/painting/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-printmaking-2-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/printmaking-2/bfa/"),
    ("bu-academics-cfa-school-of-theatre-scene-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/scene-design/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-sculpture-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/sculpture/bfa/"),
    ("bu-academics-cfa-school-of-theatre-sound-design-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/sound-design/bfa/"),
    ("bu-academics-cfa-school-of-theatre-stage-management-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/stage-management/bfa/"),
    ("bu-academics-cfa-school-of-theatre-technical-production-bfa", "CFA", "BFA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/technical-production/bfa/"),
    ("bu-academics-cfa-school-of-visual-arts-bfa-ma", "CFA", "BFA/MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/bfa-ma/"),
    ("bu-academics-cfa-school-of-theatre-theatre-arts-bfa-design-production", "CFA", "BFA—Design &amp; Production", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/theatre-arts/bfa-design-production/"),
    ("bu-academics-cfa-school-of-theatre-theatre-arts-bfa-performance", "CFA", "BFA—Performance", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-theatre/theatre-arts/bfa-performance/"),
    ("bu-academics-cfa-school-of-music-composition-bm", "CFA", "BM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/composition/bm/"),
    ("bu-academics-cfa-school-of-music-music-education-bm", "CFA", "BM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/bm/"),
    ("bu-academics-cfa-school-of-music-performance-bm", "CFA", "BM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/cfa/programs/school-of-music/performance/bm/"),
    ("bu-academics-cfa-school-of-music-music-education-bm-mm", "CFA", "BM-to-MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/bm-mm/"),
    ("bu-academics-cfa-school-of-music-music-education-cags", "CFA", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/cags/"),
    ("bu-academics-cfa-school-of-music-composition-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/composition/dma/"),
    ("bu-academics-cfa-school-of-music-conducting-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/conducting/dma/"),
    ("bu-academics-cfa-school-of-music-historical-performance-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/historical-performance/dma/"),
    ("bu-academics-cfa-school-of-music-performance-dma", "CFA", "DMA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/performance/dma/"),
    ("bu-academics-cfa-school-of-visual-arts-art-education-online-ma-in-art-education", "CFA", "MA", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/art-education/online-ma-in-art-education/"),
    ("bu-academics-cfa-school-of-visual-arts-art-education-art-education-with-initial-license", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/art-education/art-education-with-initial-license/"),
    ("bu-academics-cfa-school-of-visual-arts-museum-education", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-visual-arts/museum-education/"),
    ("bu-academics-cfa-school-of-music-musicology-ma", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/musicology/ma/"),
    ("bu-academics-cfa-school-of-music-music-theory", "CFA", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-theory/"),
    ("bu-academics-cfa-school-of-music-composition-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/composition/mm/"),
    ("bu-academics-cfa-school-of-music-conducting-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/conducting/mm/"),
    ("bu-academics-cfa-school-of-music-historical-performance-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/historical-performance/mm/"),
    ("bu-academics-cfa-school-of-music-musicology-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/musicology/mm/"),
    ("bu-academics-cfa-school-of-music-music-education-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/music-education/mm/"),
    ("bu-academics-cfa-school-of-music-performance-mm", "CFA", "MM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/cfa/programs/school-of-music/performance/mm/"),
    ("bu-academics-cfa-school-of-music-musicology-phd", "CFA", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/cfa/programs/school-of-music/musicology/phd/"),
    ("bu-cgs-liberal-arts-bs", "CGS", "Liberal Arts", "bachelors", "College of General Studies", "on_campus", 24, "https://www.bu.edu/academics/cgs/programs/september-program/"),
    ("bu-cgs-january-liberal-arts-bs", "CGS", "Liberal Arts (January Program)", "bachelors", "College of General Studies", "on_campus", 24, "https://www.bu.edu/academics/cgs/programs/september-program/"),
    ("bu-academics-com-advertising-advertising-bs", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/advertising/advertising-bs/"),
    ("bu-academics-com-film-television-film-televisionbs", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/film-television/film-televisionbs/"),
    ("bu-academics-com-journalism-bs", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/journalism/bs/"),
    ("bu-academics-com-media-science-bs-in-media-science", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/media-science/bs-in-media-science/"),
    ("bu-academics-com-public-relations-bs-in-public-relations", "COM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/com/programs/public-relations/bs-in-public-relations/"),
    ("bu-academics-com-emerging-media-studies-ma", "COM", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/emerging-media-studies/ma"),
    ("bu-academics-com-advertising-advertising-ms", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/advertising/advertising-ms/"),
    ("bu-academics-com-journalism-ms", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/journalism/ms/"),
    ("bu-academics-com-media-science-ms-in-media-science", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/media-science/ms-in-media-science/"),
    ("bu-academics-com-ms", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/ms/"),
    ("bu-academics-com-public-relations-ms-in-public-relations", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/public-relations/ms-in-public-relations/"),
    ("bu-academics-com-television", "COM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/com/programs/television/"),
    ("bu-academics-com-emerging-media-studies-phd", "COM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/com/programs/emerging-media-studies/phd"),
    ("bu-academics-eng-biomedical-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/bs/"),
    ("bu-academics-eng-computer-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/computer-engineering/bs/"),
    ("bu-academics-eng-electrical-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/electrical-engineering/bs/"),
    ("bu-academics-eng-mechanical-engineering-bs", "ENG", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/eng/programs/mechanical-engineering/bs/"),
    ("bu-academics-eng-product-design-manufacture-msmba", "ENG", "MBA/MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/product-design-manufacture/msmba/"),
    ("bu-academics-eng-biomedical-engineering-meng", "ENG", "MEng", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/meng/"),
    ("bu-academics-eng-materials-science-engineering-meng", "ENG", "MEng", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/materials-science-engineering/meng/"),
    ("bu-academics-eng-systems-engineering-meng", "ENG", "MEng", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/systems-engineering/meng/"),
    ("bu-academics-eng-biomedical-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/ms/"),
    ("bu-academics-eng-computer-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/computer-engineering/ms/"),
    ("bu-academics-eng-electrical-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/electrical-engineering/ms/"),
    ("bu-academics-eng-materials-science-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/materials-science-engineering/ms/"),
    ("bu-academics-eng-mechanical-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/mechanical-engineering/ms/"),
    ("bu-academics-eng-product-design-manufacture-product-design-manufacture", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/product-design-manufacture/product-design-manufacture/"),
    ("bu-academics-eng-systems-engineering-ms", "ENG", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/eng/programs/systems-engineering/ms/"),
    ("bu-academics-eng-biomedical-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/biomedical-engineering/phd/"),
    ("bu-academics-eng-computer-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/computer-engineering/phd/"),
    ("bu-academics-eng-electrical-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/electrical-engineering/phd/"),
    ("bu-academics-eng-materials-science-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/materials-science-engineering/phd/"),
    ("bu-academics-eng-mechanical-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/mechanical-engineering/phd/"),
    ("bu-academics-eng-systems-engineering-phd", "ENG", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/eng/programs/systems-engineering/phd/"),
    ("bu-academics-gms-dermatology", "GMS", "DSC", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/dermatology/"),
    ("bu-academics-gms-mental-health-counseling-behavioral-medicine-program-ma", "GMS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/mental-health-counseling-behavioral-medicine-program/ma/"),
    ("bu-academics-gms-anatomy-neurobiology-mdphd", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/mdphd/"),
    ("bu-academics-gms-biochemistry-mdphd", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/biochemistry/mdphd/"),
    ("bu-academics-gms-mdphd-in-bioinformatics", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/mdphd-in-bioinformatics/"),
    ("bu-academics-gms-chemistry", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/chemistry/"),
    ("bu-academics-gms-genetics-genomics", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/genetics-genomics/"),
    ("bu-academics-gms-molecular-medicine", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/molecular-medicine/"),
    ("bu-academics-gms-pathology-laboratory-medicine-phd", "GMS", "MD/PhD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/pathology-laboratory-medicine/phd/"),
    ("bu-academics-gms-anatomy-neurobiology-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/ms/"),
    ("bu-academics-gms-bioimaging", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/bioimaging/"),
    ("bu-academics-gms-biomedical-forensic-sciences", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/biomedical-forensic-sciences/"),
    ("bu-academics-gms-ms-in-biomedical-research-technologies", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/ms-in-biomedical-research-technologies/"),
    ("bu-academics-gms-clinical-investigation-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/clinical-investigation/ms/"),
    ("bu-academics-gms-forensic-anthropology", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/forensic-anthropology/"),
    ("bu-academics-gms-genetic-counseling", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/genetic-counseling/"),
    ("bu-academics-gms-healthcare-emergency-management", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/healthcare-emergency-management/"),
    ("bu-academics-gms-medical-anthropology-and-cross-cultural-practice", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/medical-anthropology-and-cross-cultural-practice/"),
    ("bu-academics-gms-medical-sciences-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/medical-sciences/ms/"),
    ("bu-academics-gms-medical-sciences-dual-degree-masters-program-in-medical-sciences-and-mental-health-counseling-behaviora", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/medical-sciences/dual-degree-masters-program-in-medical-sciences-and-mental-health-counseling-behavioral-medicine/"),
    ("bu-academics-gms-nutrition-metabolism-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/nutrition-metabolism/ms/"),
    ("bu-academics-gms-oral-health-sciences-ms", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/oral-health-sciences-ms/"),
    ("bu-academics-gms-pathology-laboratory-medicine-ma", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/pathology-laboratory-medicine/ma/"),
    ("bu-academics-gms-physician-assistant", "GMS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/gms/programs/physician-assistant/"),
    ("bu-academics-gms-anatomy-neurobiology-phd", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/phd/"),
    ("bu-academics-gms-behavioral-neuroscience", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/behavioral-neuroscience/"),
    ("bu-academics-gms-biochemistry-phd", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/biochemistry/phd/"),
    ("bu-academics-gms-pibs", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/pibs/"),
    ("bu-academics-gms-neuroscience", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/neuroscience/"),
    ("bu-academics-gms-nutrition-metabolism-phd", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/nutrition-metabolism/phd/"),
    ("bu-academics-gms-oral-biology", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/oral-biology/"),
    ("bu-academics-gms-pharmacology-experimental-therapeutics", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/pharmacology-experimental-therapeutics/"),
    ("bu-academics-gms-physiology-biophysics", "GMS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/gms/programs/physiology-biophysics/"),
    ("bu-academics-gms-virology-immunology-microbiology-program", "GMS", "PhD", "phd", "Programs", "on_campus", 48, "https://www.bu.edu/academics/gms/programs/virology-immunology-microbiology-program/"),
    ("bu-academics-grs-african-american-studies", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/african-american-studies/"),
    ("bu-academics-grs-anthropology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/anthropology/ma/"),
    ("bu-academics-grs-archaeology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/archaeology/ma/"),
    ("bu-academics-grs-history-art-architecture-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/history-art-architecture/ma/"),
    ("bu-academics-grs-astronomy-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/astronomy/ma/"),
    ("bu-academics-grs-chemistry-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/chemistry/ma/"),
    ("bu-academics-grs-classical-studies-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/classical-studies/ma/"),
    ("bu-academics-grs-classical-studies-ma-in-classics-archaeology", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/classical-studies/ma-in-classics-archaeology/"),
    ("bu-academics-grs-cognitive-neural-systems-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/cognitive-neural-systems/ma/"),
    ("bu-academics-grs-economics-ma-global-development-economics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma-global-development-economics/"),
    ("bu-academics-grs-editorial-studies-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/editorial-studies/ma/"),
    ("bu-academics-grs-english-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/english/ma/"),
    ("bu-academics-grs-romance-studies-ma-french", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/romance-studies/ma-french/"),
    ("bu-academics-grs-earth-environment-geoarchaeology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/geoarchaeology-ma/"),
    ("bu-academics-grs-romance-studies-ma-hispanic", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/romance-studies/ma-hispanic/"),
    ("bu-academics-grs-history-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/history/ma/"),
    ("bu-academics-grs-international-relations-international-affairs-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/international-relations/international-affairs-ma/"),
    ("bu-academics-grs-international-relations", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/international-relations/"),
    ("bu-academics-grs-latin-american-studies-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/latin-american-studies-ma/"),
    ("bu-academics-grs-linguistics-ma-in-linguistics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/linguistics/ma-in-linguistics/"),
    ("bu-academics-grs-mathematics-statistics-ma-mathematics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/ma-mathematics/"),
    ("bu-academics-grs-molecular-biology-cell-biology-biochemistry-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/molecular-biology-cell-biology-biochemistry/ma/"),
    ("bu-academics-grs-neuroscience-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/neuroscience/ma/"),
    ("bu-academics-grs-philosophy-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/philosophy/ma/"),
    ("bu-academics-grs-physics-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/physics/ma/"),
    ("bu-academics-grs-political-science-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/political-science/ma/"),
    ("bu-academics-grs-preservation-studies", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/preservation-studies/"),
    ("bu-academics-grs-psychology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/psychology/ma/"),
    ("bu-academics-grs-religious-studies-ma-in-religious-studies", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/religious-studies/ma-in-religious-studies/"),
    ("bu-academics-grs-sociology-ma", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/sociology/ma/"),
    ("bu-academics-grs-mathematics-statistics-ma-statistics", "GRS", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/ma-statistics/"),
    ("bu-academics-grs-international-relations-international-relations-ma-mba", "GRS", "MA/MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/international-relations/international-relations-ma-mba/"),
    ("bu-academics-grs-classical-studies-ma-phd-phil", "GRS", "MA/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/classical-studies/ma-phd-phil/"),
    ("bu-academics-grs-economics-ma-phd", "GRS", "MA/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/economics/ma-phd/"),
    ("bu-academics-grs-computer-science-ms-in-artificial-intelligence", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/computer-science/ms-in-artificial-intelligence/"),
    ("bu-academics-grs-biology-master-of-science-in-biology", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/biology/master-of-science-in-biology//"),
    ("bu-academics-grs-biostatistics-ms", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/biostatistics/ms/"),
    ("bu-academics-grs-computer-science-ms", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/computer-science/ms/"),
    ("bu-academics-grs-economics-ma-economic-policy", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma-economic-policy/"),
    ("bu-academics-grs-economics-ma", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma/"),
    ("bu-academics-grs-earth-environment-ma-energy-environment", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/ma-energy-environment/"),
    ("bu-academics-grs-earth-environment-ma-remote-sensing", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/ma-remote-sensing/"),
    ("bu-academics-grs-mathematics-statistics-ms-in-statistical-practice", "GRS", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/ms-in-statistical-practice/"),
    ("bu-academics-grs-economics-ma-mba", "GRS", "MS/MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/economics/ma-mba/"),
    ("bu-academics-grs-earth-environment-ma-in-energy-environment-mba-dual-degree-program", "GRS", "MS/MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/grs/programs/earth-environment/ma-in-energy-environment-mba-dual-degree-program/"),
    ("bu-academics-grs-american-new-england-studies", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/american-new-england-studies/"),
    ("bu-academics-grs-anthropology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/anthropology/phd/"),
    ("bu-academics-grs-archaeology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/archaeology/phd/"),
    ("bu-academics-grs-history-art-architecture-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/history-art-architecture/phd/"),
    ("bu-academics-grs-astronomy-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/astronomy/phd/"),
    ("bu-academics-grs-biology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/biology/phd/"),
    ("bu-academics-grs-biostatistics-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/biostatistics/phd/"),
    ("bu-academics-grs-chemistry-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/chemistry/phd/"),
    ("bu-academics-grs-classical-studies-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/classical-studies/phd/"),
    ("bu-academics-grs-cognitive-neural-systems-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/cognitive-neural-systems/phd/"),
    ("bu-academics-grs-computer-science-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/computer-science/phd"),
    ("bu-academics-grs-editorial-studies-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/editorial-studies/phd/"),
    ("bu-academics-grs-english-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/english/phd/"),
    ("bu-academics-grs-romance-studies-phd-french", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/romance-studies/phd-french/"),
    ("bu-academics-grs-romance-studies-phd-hispanic", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/romance-studies/phd-hispanic/"),
    ("bu-academics-grs-history-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/history/phd/"),
    ("bu-academics-grs-linguistics-phd-in-linguistics", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/linguistics/phd-in-linguistics/"),
    ("bu-academics-grs-mathematics-statistics-phd-mathematics", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/phd-mathematics/"),
    ("bu-academics-grs-molecular-biology-cell-biology-biochemistry-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/molecular-biology-cell-biology-biochemistry/phd/"),
    ("bu-academics-grs-neuroscience-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/neuroscience/phd/"),
    ("bu-academics-grs-philosophy-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/philosophy/phd/"),
    ("bu-academics-grs-physics-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/physics/phd/"),
    ("bu-academics-grs-political-science-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/political-science/phd/"),
    ("bu-academics-grs-psychology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/psychology/phd/"),
    ("bu-academics-grs-religion", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/religion/"),
    ("bu-academics-grs-sociology-phd", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/sociology/phd/"),
    ("bu-academics-grs-sociology-sociology-social-work", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/sociology/sociology-social-work/"),
    ("bu-academics-grs-mathematics-statistics-phd-statistics", "GRS", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/grs/programs/mathematics-statistics/phd-statistics/"),
    ("bu-academics-law-jd", "LAW", "JD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jd/"),
    ("bu-academics-law-accelerated-llm-in-banking-financial-law", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/accelerated-llm-in-banking-financial-law/"),
    ("bu-academics-law-jdllm-in-european-law-at-paris-ii", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdllm-in-european-law-at-paris-ii/"),
    ("bu-academics-law-jdllm-in-finance", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdllm-in-finance/"),
    ("bu-academics-law-jd-llm-in-international-commercial-and-investment-arbitration-at-paris2", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jd-llm-in-international-commercial-and-investment-arbitration-at-paris2/"),
    ("bu-academics-law-jdllm-in-international-and-european-business-law-at-icade", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdllm-in-international-and-european-business-law-at-icade/"),
    ("bu-academics-law-accelerated-llm-in-taxation", "LAW", "JD/LLM", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/accelerated-llm-in-taxation/"),
    ("bu-academics-law-jdma-english", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-english/"),
    ("bu-academics-law-jdma-history", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-history/"),
    ("bu-academics-law-jdma-ir", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-ir/"),
    ("bu-academics-law-jdma-philosophy", "LAW", "JD/MA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-philosophy/"),
    ("bu-academics-law-jdmba", "LAW", "JD/MBA", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdmba/"),
    ("bu-academics-law-jdmba-health", "LAW", "JD/MBA—Health Sector Management", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdmba-health/"),
    ("bu-academics-law-jdmph", "LAW", "JD/MPH", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdmph/"),
    ("bu-academics-law-american-law", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/american-law/"),
    ("bu-academics-law-graduate-program-in-banking-financial-law", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/graduate-program-in-banking-financial-law/"),
    ("bu-academics-law-intellectual-property-law", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/intellectual-property-law/"),
    ("bu-academics-law-graduate-tax-program", "LAW", "LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/graduate-tax-program/"),
    ("bu-academics-law-jdma-preservation", "LAW", "MA/JD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/law/programs/jdma-preservation/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-american-law", "LAW", "Two-Year LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-american-law/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-banking-financial-law", "LAW", "Two-Year LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-banking-financial-law/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-intellectual-property-information-law", "LAW", "Two-Year LLM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-intellectual-property-information-law/"),
    ("bu-academics-law-two-year-master-of-laws-llm-in-tax-law", "LAW", "Two-Year MSL-TAX", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/law/programs/two-year-master-of-laws-llm-in-tax-law/"),
    ("bu-academics-met-biology", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/biology/"),
    ("bu-academics-met-computer-science-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/computer-science/bs/"),
    ("bu-academics-met-criminal-justice-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/criminal-justice/bs/"),
    ("bu-academics-met-economics", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/economics/"),
    ("bu-academics-met-interdisciplinary-studies", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/interdisciplinary-studies/"),
    ("bu-academics-met-administrative-sciences-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/administrative-sciences/bs/"),
    ("bu-academics-met-mathematics", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/mathematics/"),
    ("bu-academics-met-psychology", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/psychology/"),
    ("bu-academics-met-sociology-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/sociology/bs/"),
    ("bu-academics-met-urban-affairs-bs", "MET", "BS", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/urban-affairs/bs/"),
    ("bu-academics-met-gastronomy", "MET", "MA", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/gastronomy/"),
    ("bu-academics-met-actuarial-science-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/actuarial-science/ms/"),
    ("bu-academics-met-advertising", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/advertising/"),
    ("bu-academics-met-computer-science-master-of-science-in-applied-data-analytics", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/master-of-science-in-applied-data-analytics/"),
    ("bu-academics-met-arts-administration-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/arts-administration/ms/"),
    ("bu-academics-met-computer-science-mscis", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/mscis/"),
    ("bu-academics-met-computer-science-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/ms/"),
    ("bu-academics-met-criminal-justice-mcj", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/criminal-justice/mcj/"),
    ("bu-academics-met-health-communication-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/health-communication/ms/"),
    ("bu-academics-met-computer-science-ms-in-health-informatics", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/ms-in-health-informatics/"),
    ("bu-academics-met-administrative-sciences-ms-in-human-resources-management", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms-in-human-resources-management/"),
    ("bu-academics-met-administrative-sciences-ms", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms/"),
    ("bu-academics-met-administrative-sciences-ms-insurance-management", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms-insurance-management/"),
    ("bu-academics-met-administrative-sciences-ms-project-management", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/administrative-sciences/ms-project-management/"),
    ("bu-academics-met-computer-science-ms-in-software-development", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/ms-in-software-development/"),
    ("bu-academics-met-computer-science-telecommunication", "MET", "MS", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/met/programs/computer-science/telecommunication/"),
    ("bu-academics-met-computer-science-bs-accelerated", "MET", "accelerated degree completion program", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/computer-science/bs-accelerated/"),
    ("bu-academics-met-administrative-sciences-bs-accelerated", "MET", "accelerated degree completion program", "bachelors", "Programs", "online", 48, "https://www.bu.edu/academics/met/programs/administrative-sciences/bs-accelerated/"),
    ("bu-academics-questrom-undergrad", "QUESTROM", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/questrom/programs/undergrad/"),
    ("bu-academics-questrom-bachelor-of-science-in-business-administration-bsba-to-master-of-science-in-business-analytics-msb", "QUESTROM", "BSBA-to-MSBA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/questrom/programs/bachelor-of-science-in-business-administration-bsba-to-master-of-science-in-business-analytics-msba-program/"),
    ("bu-academics-questrom-mba", "QUESTROM", "MBA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/mba/"),
    ("bu-academics-questrom-msdt", "QUESTROM", "MBA/MSDT", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/msdt/"),
    ("bu-academics-questrom-ms-in-business-analytics", "QUESTROM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/ms-in-business-analytics/"),
    ("bu-academics-questrom-ms-in-finance", "QUESTROM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/ms-in-finance/"),
    ("bu-academics-questrom-mathematical-finance-ms", "QUESTROM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/mathematical-finance/ms/"),
    ("bu-academics-questrom-ms-in-management-studies", "QUESTROM", "MiM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/questrom/programs/ms-in-management-studies/"),
    ("bu-academics-questrom-phd-in-management", "QUESTROM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/questrom/programs/phd-in-management/"),
    ("bu-academics-questrom-phd-in-business-economics", "QUESTROM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/questrom/programs/phd-in-business-economics/"),
    ("bu-academics-questrom-mathematical-finance-phd", "QUESTROM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/questrom/programs/mathematical-finance/phd/"),
    ("bu-rotc-air-force-ms", "ROTC", "Aerospace Studies (Air Force ROTC)", "certificate", "Division of Military Education", "on_campus", 48, "https://www.bu.edu/academics/rotc/programs/aerospace-studies/"),
    ("bu-rotc-army-ms", "ROTC", "Military Science (Army ROTC)", "certificate", "Division of Military Education", "on_campus", 48, "https://www.bu.edu/academics/rotc/programs/military-science/"),
    ("bu-rotc-navy-ms", "ROTC", "Naval Science (Navy ROTC)", "certificate", "Division of Military Education", "on_campus", 48, "https://www.bu.edu/academics/rotc/programs/naval-science/"),
    ("bu-academics-sar-bs-in-behavior-and-health", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/bs-in-behavior-and-health/"),
    ("bu-academics-sar-health-science", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/health-science/"),
    ("bu-academics-sar-human-physiology-bs", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/human-physiology/bs/"),
    ("bu-academics-sar-speech-language-hearing-sciences-bs-in-linguistics-speech-language-and-hearing-sciences", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/bs-in-linguistics-speech-language-and-hearing-sciences/"),
    ("bu-academics-sar-nutrition-dietetics-bs", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/nutrition-dietetics/bs/"),
    ("bu-academics-sar-speech-language-hearing-sciences-bs", "SAR", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/bs/"),
    ("bu-academics-sar-human-physiology-bsms", "SAR", "BS-to-MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/human-physiology/bsms/"),
    ("bu-academics-sar-speech-language-hearing-sciences-bs-ms", "SAR", "BS-to-MS-SLP", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/bs-ms/"),
    ("bu-academics-sar-physical-therapy-bs-dpt", "SAR", "BS/DPT", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sar/programs/physical-therapy/bs-dpt/"),
    ("bu-academics-sar-physical-therapy-dpt-phd", "SAR", "DPT/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/physical-therapy/dpt-phd/"),
    ("bu-academics-sar-human-physiology-ms", "SAR", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/human-physiology/ms/"),
    ("bu-academics-sar-nutrition-dietetics-ms", "SAR", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/nutrition-dietetics/ms/"),
    ("bu-academics-sar-speech-language-hearing-sciences-ms", "SAR", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/ms/"),
    ("bu-academics-sar-speech-language-hearing-sciences-ms-phd", "SAR", "MS/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/ms-phd/"),
    ("bu-academics-sar-occupational-therapy-otd-phd", "SAR", "OTD/PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/occupational-therapy/otd-phd/"),
    ("bu-academics-sar-human-physiology-phd", "SAR", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/human-physiology/phd/"),
    ("bu-academics-sar-rehabilitation-sciences", "SAR", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/rehabilitation-sciences/"),
    ("bu-academics-sar-speech-language-hearing-sciences-phd", "SAR", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sar/programs/speech-language-hearing-sciences/phd/"),
    ("bu-academics-sar-public-health-bs-mph", "SAR", "minor", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sar/programs/public-health/bs-mph/"),
    ("bu-academics-sdm-dental-public-health-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/dental-public-health/cags/"),
    ("bu-academics-sdm-endodontics-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/endodontics/cags/"),
    ("bu-academics-sdm-operative-dentistry-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/operative-dentistry/cags/"),
    ("bu-academics-sdm-oral-and-maxillofacial-surgery-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/oral-and-maxillofacial-surgery/cags/"),
    ("bu-academics-sdm-pediatric-dentistry-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/cags/"),
    ("bu-academics-sdm-periodontology-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/periodontology/cags/"),
    ("bu-academics-sdm-prosthodontics-cags", "SDM", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/prosthodontics/cags/"),
    ("bu-academics-sdm-doctor-of-dental-medicine", "SDM", "DMD", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sdm/programs/doctor-of-dental-medicine/"),
    ("bu-academics-sdm-oral-biology-dsc", "SDM", "DSc", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/oral-biology/dsc/"),
    ("bu-academics-sdm-dscd-dental-biomaterials", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/dscd-dental-biomaterials/"),
    ("bu-academics-sdm-endodontics-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/endodontics/dscd/"),
    ("bu-academics-sdm-operative-dentistry-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/operative-dentistry/dscd/"),
    ("bu-academics-sdm-oral-and-maxillofacial-surgery-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/oral-and-maxillofacial-surgery/dscd/"),
    ("bu-academics-sdm-orthodontics-dentofacial-orthopedics-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/orthodontics-dentofacial-orthopedics/dscd/"),
    ("bu-academics-sdm-pediatric-dentistry-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/dscd/"),
    ("bu-academics-sdm-periodontology-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/periodontology/dscd/"),
    ("bu-academics-sdm-prosthodontics-cags-dscd", "SDM", "DScD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/prosthodontics/cags-dscd"),
    ("bu-academics-sdm-dental-biomaterials-dscd-cags", "SDM", "DScD/CAGS", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/dental-biomaterials/dscd-cags/"),
    ("bu-academics-sdm-dental-public-health-dscd", "SDM", "DScD/CAGS", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/dental-public-health/dscd/"),
    ("bu-academics-sdm-dental-public-health-ms", "SDM", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/dental-public-health/ms/"),
    ("bu-academics-sdm-dental-public-health-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/dental-public-health/msd/"),
    ("bu-academics-sdm-endodontics-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/endodontics/msd/"),
    ("bu-academics-sdm-operative-dentistry-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/operative-dentistry/msd/"),
    ("bu-academics-sdm-oral-biology-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/oral-biology/msd/"),
    ("bu-academics-sdm-oral-and-maxillofacial-surgery-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/oral-and-maxillofacial-surgery/msd/"),
    ("bu-academics-sdm-orthodontics-dentofacial-orthopedics-cags-msd", "SDM", "MSD", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/orthodontics-dentofacial-orthopedics/cags-msd/"),
    ("bu-academics-sdm-pediatric-dentistry-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/msd/"),
    ("bu-academics-sdm-periodontology-msd", "SDM", "MSD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sdm/programs/periodontology/msd/"),
    ("bu-academics-sdm-prosthodontics-cags-msd", "SDM", "MSD", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/prosthodontics/cags-msd"),
    ("bu-academics-sdm-dental-biomaterials-msd-cags", "SDM", "MSD/CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/sdm/programs/dental-biomaterials/msd-cags/"),
    ("bu-academics-sdm-oral-biology-phd", "SDM", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sdm/programs/oral-biology/phd/"),
    ("bu-academics-sha-bachelor-of-science-in-hospitality-administration", "SHA", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sha/programs/bachelor-of-science-in-hospitality-administration/"),
    ("bu-academics-sha-bs-in-hospitality-communication", "SHA", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sha/programs/bs-in-hospitality-communication/"),
    ("bu-academics-sha-bs-mla", "SHA", "BS/MLA", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sha/programs/bs-mla/"),
    ("bu-academics-sha-ms", "SHA", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sha/programs/ms/"),
    ("bu-academics-sph-mba-mph", "SPH", "MBA/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mba-mph/"),
    ("bu-academics-sph-medicine-and-public-health", "SPH", "MD/MPH", "professional", "Programs", "on_campus", 48, "https://www.bu.edu/academics/sph/programs/medicine-and-public-health/"),
    ("bu-academics-sph-mph-chronic-and-non-communicable-diseases", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/chronic-and-non-communicable-diseases/"),
    ("bu-academics-sph-mph-community-assessment", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/community-assessment/"),
    ("bu-academics-sph-mph-environmental-health", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/environmental-health/"),
    ("bu-academics-sph-mph-epidemiology-and-biostatistics", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/epidemiology-and-biostatistics/"),
    ("bu-academics-sph-mph-global-health-2", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/global-health-2/"),
    ("bu-academics-sph-mph-monitoring-and-evaluation", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/monitoring-and-evaluation/"),
    ("bu-academics-sph-mph-healthcare-management", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/healthcare-management/"),
    ("bu-academics-sph-programs-health-communication-and-promotion", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/programs/health-communication-and-promotion/"),
    ("bu-academics-sph-mph-in-health-equity", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph-in-health-equity/"),
    ("bu-academics-sph-mph-health-policy-and-law", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/health-policy-and-law/"),
    ("bu-academics-sph-mph-human-rights-and-social-justice", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/human-rights-and-social-justice/"),
    ("bu-academics-sph-mph-infectious-disease", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/infectious-disease/"),
    ("bu-academics-sph-mph-maternal-and-child-health", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/maternal-and-child-health/"),
    ("bu-academics-sph-mph-mental-health-and-substance-use", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/mental-health-and-substance-use/"),
    ("bu-academics-sph-mph-pharmaceutical-development-delivery-and-access", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/pharmaceutical-development-delivery-and-access/"),
    ("bu-academics-sph-mph", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/"),
    ("bu-academics-sph-mph-sex-sexuality-and-gender", "SPH", "MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/mph/sex-sexuality-and-gender/"),
    ("bu-academics-sph-ms-in-genetic-counseling-master-of-public-health-ms-mph", "SPH", "MS/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/ms-in-genetic-counseling-master-of-public-health-ms-mph/"),
    ("bu-academics-sph-medical-sciences-and-public-health", "SPH", "MS/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/medical-sciences-and-public-health/"),
    ("bu-academics-sph-social-work-and-public-health", "SPH", "MSW/MPH", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sph/programs/social-work-and-public-health/"),
    ("bu-academics-sph-environmental-health-phd", "SPH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sph/programs/environmental-health/phd/"),
    ("bu-academics-sph-epidemiology-phd", "SPH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sph/programs/epidemiology/phd/"),
    ("bu-academics-sph-health-services-research-phd", "SPH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sph/programs/health-services-research/phd/"),
    ("bu-academics-ssw-clinical-social-work-practice", "SSW", "MSW", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/clinical-social-work-practice/"),
    ("bu-academics-ssw-macro-social-work-practice", "SSW", "MSW", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/macro-social-work-practice/"),
    ("bu-academics-ssw-msw", "SSW", "MSW Online", "masters", "Programs", "online", 24, "https://www.bu.edu/academics/ssw/programs/msw/"),
    ("bu-academics-ssw-dual-degree-programs-in-social-work-and-education", "SSW", "MSW/EdD", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/dual-degree-programs-in-social-work-and-education/"),
    ("bu-academics-ssw-dual-degree-in-theology-and-social-work", "SSW", "MSW/MTS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/ssw/programs/dual-degree-in-theology-and-social-work/"),
    ("bu-academics-ssw-phd-in-social-work", "SSW", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/ssw/programs/phd-in-social-work/"),
    ("bu-academics-sth-marpl", "STH", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/sth/programs/marpl/"),
    ("bu-academics-sth-theological-studies-phd", "STH", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/sth/programs/theological-studies-phd/"),
    ("bu-academics-wheelock-bilingual-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/bs/"),
    ("bu-academics-wheelock-deaf-studies-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/deaf-studies/bs/"),
    ("bu-academics-wheelock-early-childhood-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/early-childhood-education/bs/"),
    ("bu-academics-wheelock-bs-in-education-human-development", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/bs-in-education-human-development/"),
    ("bu-academics-wheelock-elementary-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/elementary-education/bs/"),
    ("bu-academics-wheelock-english-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/english-education/bs/"),
    ("bu-academics-wheelock-mathematics-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/mathematics-education/bs/"),
    ("bu-academics-wheelock-modern-foreign-language-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/modern-foreign-language-education/bs/"),
    ("bu-academics-wheelock-science-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/science-education/bs/"),
    ("bu-academics-wheelock-social-studies-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/social-studies-education/bs/"),
    ("bu-academics-wheelock-special-education-bs", "WHEEL", "BS", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/special-education/bs/"),
    ("bu-academics-wheelock-applied-human-development-bs-edm-applied-human-development", "WHEEL", "BS-to-EdM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/applied-human-development/bs-edm-applied-human-development/"),
    ("bu-academics-wheelock-bilingual-education-bs-edm-tesol-applied-linguistics", "WHEEL", "BS-to-EdM", "bachelors", "Programs", "on_campus", 48, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/bs-edm-tesol-applied-linguistics/"),
    ("bu-academics-wheelock-bilingual-education-bs-ms-tesol-multilingual-learner-education", "WHEEL", "BS-to-EdM", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/bs-ms-tesol-multilingual-learner-education/"),
    ("bu-academics-wheelock-policy-planning-administration-bs-ma-educational-policy-studies", "WHEEL", "BS-to-MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/policy-planning-administration/bs-ma-educational-policy-studies/"),
    ("bu-academics-wheelock-bilingual-education", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/bilingual-education/"),
    ("bu-academics-wheelock-curriculum-teaching-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/curriculum-teaching/cags/"),
    ("bu-academics-wheelock-deaf-studies-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/deaf-studies/cags/"),
    ("bu-academics-wheelock-developmental-studies-cags-lit-language", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/developmental-studies/cags-lit-language/"),
    ("bu-academics-wheelock-early-childhood-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/early-childhood-education/cags/"),
    ("bu-academics-wheelock-policy-planning-administration-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/policy-planning-administration/cags/"),
    ("bu-academics-wheelock-english-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/english-education/cags/"),
    ("bu-academics-wheelock-literacy-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/literacy-education/cags/"),
    ("bu-academics-wheelock-science-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/science-education/cags/"),
    ("bu-academics-wheelock-social-studies-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/social-studies-education/cags/"),
    ("bu-academics-wheelock-special-education-cags", "WHEEL", "CAGS", "certificate", "Programs", "on_campus", 12, "https://www.bu.edu/academics/wheelock/programs/special-education/cags/"),
    ("bu-academics-wheelock-policy-planning-administration-ma-in-educational-policy-studies", "WHEEL", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/policy-planning-administration/ma-in-educational-policy-studies/"),
    ("bu-academics-wheelock-early-childhood-education-ma-in-leadership-policy-advocacy-for-early-childhood-well-being", "WHEEL", "MA", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/early-childhood-education/ma-in-leadership-policy-advocacy-for-early-childhood-well-being/"),
    ("bu-academics-wheelock-ms-in-child-life-family-centered-care", "WHEEL", "MS", "masters", "Programs", "on_campus", 24, "https://www.bu.edu/academics/wheelock/programs/ms-in-child-life-family-centered-care/"),
    ("bu-academics-wheelock-applied-human-development-phd-counseling-psychology-applied-human-development", "WHEEL", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/wheelock/programs/applied-human-development/phd-counseling-psychology-applied-human-development/"),
    ("bu-academics-wheelock-deaf-studies", "WHEEL", "PhD", "phd", "Programs", "on_campus", 60, "https://www.bu.edu/academics/wheelock/programs/deaf-studies/")
]

_DEGREE_TOKENS = frozenset({
    "ba", "bs", "bfa", "bm", "bachelors", "ms", "ma", "mph", "msw", "meng", "mba", "mm",
    "msd", "cags", "phd", "dsc", "dscd", "dmd", "jd", "md", "minor", "online",
})
_LEGACY_COUNTS = Counter(name for _s, _sk, name, *_ in _CATALOG)
_PROGRAM_NAME_OVERRIDES: dict[str, str] = {
    "bu-academics-busm-four-year-program": "Doctor of Medicine",
    "bu-academics-law-jd": "Juris Doctor",
    "bu-academics-questrom-mba": "Master of Business Administration",
    "bu-academics-sdm-doctor-of-dental-medicine": "Doctor of Dental Medicine",
    "bu-academics-com-ms": "Master of Science in Communication",
    "bu-academics-sha-ms": "Master of Science in Hospitality Administration",
    "bu-academics-sph-mph": "Master of Public Health",
    "bu-academics-sph-programs-health-communication-and-promotion": (
        "Master of Public Health in Health Communication and Promotion"
    ),
    "bu-academics-com-advertising-advertising-bs": "Bachelor of Science in Advertising",
    "bu-academics-met-computer-science-bs": "Bachelor of Science in Computer Science",
    "bu-academics-met-sociology-bs": "Bachelor of Science in Sociology",
    "bu-academics-wheelock-science-education-bs": "Bachelor of Science in Science Education",
    "bu-academics-wheelock-applied-human-development-bs-edm-applied-human-development": (
        "Bachelor of Science in Applied Human Development"
    ),
    "bu-academics-wheelock-bilingual-education-bs-edm-tesol-applied-linguistics": (
        "Bachelor of Science in Bilingual Education"
    ),
    # --- Law J.D./M.A. duals: real names (never the bare "Jdma <field>" URL token). ---
    "bu-academics-law-jdma-english": "Juris Doctor / Master of Arts in English",
    "bu-academics-law-jdma-history": "Juris Doctor / Master of Arts in History",
    "bu-academics-law-jdma-ir": "Juris Doctor / Master of Arts in International Relations",
    "bu-academics-law-jdma-philosophy": "Juris Doctor / Master of Arts in Philosophy",
    # GMS virology/immunology/microbiology PhD — never the bare "PhD, MD/PhD" credential combo.
    "bu-academics-gms-virology-immunology-microbiology-program": (
        "Doctor of Philosophy in Virology, Immunology & Microbiology"
    ),
    # --- Dual / joint / accelerated degrees: real names (never a bare credential combo). ---
    "bu-academics-busm-combined-mdjd": "Doctor of Medicine / Juris Doctor (MD/JD)",
    "bu-academics-busm-combined-md-mba": "Doctor of Medicine / Master of Business Administration (MD/MBA)",
    "bu-academics-busm-md-phd-combined-degree": "Doctor of Medicine / Doctor of Philosophy (MD/PhD)",
    "bu-academics-sar-public-health-bs-mph": "Bachelor of Science-to-Master of Public Health",
    "bu-academics-cas-bamph-program": "Bachelor of Arts to Master of Public Health (Accelerated)",
    "bu-academics-cas-world-languages-literatures-ba-in-comparative-literature-mfa-in-literary-translation": (
        "Bachelor of Arts in Comparative Literature / Master of Fine Arts in Literary Translation"
    ),
    "bu-academics-cds-bs-data-science-ms-bioinformatics": (
        "Bachelor of Science in Data Science to Master of Science in Bioinformatics (Accelerated)"
    ),
    "bu-academics-cfa-school-of-visual-arts-bfa-ma": (
        "Bachelor of Fine Arts to Master of Arts in Visual Arts (Accelerated)"
    ),
    "bu-academics-cfa-school-of-theatre-theatre-arts-bfa-design-production": (
        "Bachelor of Fine Arts in Theatre Arts — Design & Production"
    ),
    "bu-academics-cfa-school-of-theatre-theatre-arts-bfa-performance": (
        "Bachelor of Fine Arts in Theatre Arts — Performance"
    ),
    "bu-academics-cfa-school-of-music-music-education-bm-mm": (
        "Bachelor of Music to Master of Music in Music Education (Accelerated)"
    ),
    "bu-academics-eng-product-design-manufacture-msmba": (
        "Master of Science in Product Design & Manufacture / Master of Business Administration"
    ),
    "bu-academics-gms-dermatology": "Doctor of Science in Dermatology",
    "bu-academics-grs-international-relations-international-relations-ma-mba": (
        "Master of Arts in International Relations / Master of Business Administration"
    ),
    "bu-academics-law-jdmba": "Juris Doctor / Master of Business Administration (JD/MBA)",
    "bu-academics-law-jdmba-health": (
        "Juris Doctor / Master of Business Administration — Health Sector Management"
    ),
    "bu-academics-law-jdmph": "Juris Doctor / Master of Public Health (JD/MPH)",
    "bu-academics-law-jdma-preservation": "Juris Doctor / Master of Arts in Preservation Studies",
    "bu-academics-questrom-bachelor-of-science-in-business-administration-bsba-to-master-of-science-in-business-analytics-msb": (
        "Bachelor of Science in Business Administration to Master of Science in Business Analytics (Accelerated)"
    ),
    "bu-academics-questrom-msdt": "Master of Science in Digital Technology",
    "bu-academics-sar-speech-language-hearing-sciences-bs-ms": (
        "Bachelor of Science to Master of Science in Speech-Language Pathology (Accelerated)"
    ),
    "bu-academics-sar-physical-therapy-bs-dpt": (
        "Bachelor of Science to Doctor of Physical Therapy (Accelerated)"
    ),
    "bu-academics-sar-physical-therapy-dpt-phd": (
        "Doctor of Physical Therapy / Doctor of Philosophy in Rehabilitation Sciences"
    ),
    "bu-academics-sar-speech-language-hearing-sciences-ms-phd": (
        "Master of Science / Doctor of Philosophy in Speech, Language & Hearing Sciences"
    ),
    "bu-academics-sar-occupational-therapy-otd-phd": (
        "Doctor of Occupational Therapy / Doctor of Philosophy in Rehabilitation Sciences"
    ),
    "bu-academics-sdm-oral-biology-dsc": "Doctor of Science in Oral Biology",
    "bu-academics-sdm-dental-biomaterials-msd-cags": (
        "Master of Science in Dentistry / Certificate of Advanced Graduate Study in Dental Biomaterials"
    ),
    "bu-academics-sha-bs-mla": (
        "Bachelor of Science in Hospitality Administration to Master of Liberal Arts (Accelerated)"
    ),
    "bu-academics-sph-mba-mph": "Master of Business Administration / Master of Public Health (MBA/MPH)",
    "bu-academics-sph-medicine-and-public-health": "Doctor of Medicine / Master of Public Health (MD/MPH)",
    "bu-academics-sph-social-work-and-public-health": "Master of Social Work / Master of Public Health (MSW/MPH)",
    "bu-academics-ssw-dual-degree-programs-in-social-work-and-education": (
        "Master of Social Work / Doctor of Education (MSW/EdD)"
    ),
    "bu-academics-ssw-dual-degree-in-theology-and-social-work": (
        "Master of Social Work / Master of Theological Studies (MSW/MTS)"
    ),
    "bu-academics-wheelock-policy-planning-administration-bs-ma-educational-policy-studies": (
        "Bachelor of Science to Master of Arts in Educational Policy Studies (Accelerated)"
    ),
    # --- GMS combined-degree and malformed title-case rows ---
    "bu-academics-gms-anatomy-neurobiology-mdphd": (
        "Doctor of Medicine / Doctor of Philosophy in Anatomy & Neurobiology"
    ),
    "bu-academics-gms-biochemistry-mdphd": "Doctor of Medicine / Doctor of Philosophy in Biochemistry",
    "bu-academics-gms-mdphd-in-bioinformatics": "Doctor of Medicine / Doctor of Philosophy in Bioinformatics",
    "bu-academics-gms-medical-anthropology-and-cross-cultural-practice": (
        "Master of Science in Medical Anthropology & Cross-Cultural Practice"
    ),
    "bu-academics-gms-chemistry": "Master of Arts in Chemistry (Graduate Medical Sciences)",
    # --- School of Law LL.M. and joint J.D./LL.M. programs ---
    "bu-academics-law-accelerated-llm-in-banking-financial-law": (
        "Accelerated LL.M. in Banking & Financial Law"
    ),
    "bu-academics-law-jdllm-in-european-law-at-paris-ii": (
        "Juris Doctor / LL.M. in European Law (with Université Paris II)"
    ),
    "bu-academics-law-jdllm-in-finance": "Juris Doctor / LL.M. in Finance",
    "bu-academics-law-jd-llm-in-international-commercial-and-investment-arbitration-at-paris2": (
        "Juris Doctor / LL.M. in International Commercial & Investment Arbitration (with Université Paris II)"
    ),
    "bu-academics-law-jdllm-in-international-and-european-business-law-at-icade": (
        "Juris Doctor / LL.M. in International & European Business Law (with ICADE)"
    ),
    "bu-academics-law-accelerated-llm-in-taxation": "Accelerated LL.M. in Taxation",
    "bu-academics-law-graduate-program-in-banking-financial-law": (
        "Master of Laws (LL.M.) in Banking & Financial Law"
    ),
    "bu-academics-law-two-year-master-of-laws-llm-in-american-law": "Two-Year LL.M. in American Law",
    "bu-academics-law-two-year-master-of-laws-llm-in-banking-financial-law": (
        "Two-Year LL.M. in Banking & Financial Law"
    ),
    "bu-academics-law-two-year-master-of-laws-llm-in-intellectual-property-information-law": (
        "Two-Year LL.M. in Intellectual Property & Information Law"
    ),
    # --- Sargent / SDM / SHA malformed names ---
    "bu-academics-sar-bs-in-behavior-and-health": "Bachelor of Science in Behavior & Health",
    "bu-academics-sdm-oral-and-maxillofacial-surgery-cags": (
        "Certificate of Advanced Graduate Study in Oral & Maxillofacial Surgery"
    ),
    "bu-academics-sdm-oral-and-maxillofacial-surgery-dscd": (
        "Doctor of Science in Oral & Maxillofacial Surgery"
    ),
    "bu-academics-sdm-oral-and-maxillofacial-surgery-msd": (
        "Master of Science in Oral & Maxillofacial Surgery"
    ),
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration": (
        "Bachelor of Science in Hospitality Administration"
    ),
    # --- School of Public Health: M.P.H. core + concentrations (not "M.S. in Mph"). ---
    "bu-academics-sph-ms-in-genetic-counseling-master-of-public-health-ms-mph": (
        "Master of Science in Genetic Counseling / Master of Public Health"
    ),
    "bu-academics-sph-medical-sciences-and-public-health": (
        "Master of Science in Medical Sciences & Public Health"
    ),
    "bu-academics-sph-mph-in-health-equity": "Master of Public Health — Health Equity",
    "bu-academics-sph-mph-global-health-2": "Master of Public Health — Global Health",
    "bu-academics-sph-mph-chronic-and-non-communicable-diseases": (
        "Master of Public Health — Chronic & Non-Communicable Diseases"
    ),
    "bu-academics-sph-mph-community-assessment": "Master of Public Health — Community Assessment",
    "bu-academics-sph-mph-environmental-health": "Master of Public Health — Environmental Health",
    "bu-academics-sph-mph-epidemiology-and-biostatistics": (
        "Master of Public Health — Epidemiology & Biostatistics"
    ),
    "bu-academics-sph-mph-monitoring-and-evaluation": "Master of Public Health — Monitoring & Evaluation",
    "bu-academics-sph-mph-healthcare-management": "Master of Public Health — Healthcare Management",
    "bu-academics-sph-mph-health-policy-and-law": "Master of Public Health — Health Policy & Law",
    "bu-academics-sph-mph-human-rights-and-social-justice": (
        "Master of Public Health — Human Rights & Social Justice"
    ),
    "bu-academics-sph-mph-infectious-disease": "Master of Public Health — Infectious Disease",
    "bu-academics-sph-mph-maternal-and-child-health": "Master of Public Health — Maternal & Child Health",
    "bu-academics-sph-mph-mental-health-and-substance-use": (
        "Master of Public Health — Mental Health & Substance Use"
    ),
    "bu-academics-sph-mph-pharmaceutical-development-delivery-and-access": (
        "Master of Public Health — Pharmaceutical Development, Delivery & Access"
    ),
    # --- Online variants whose dedup suffix left a bare credential name ---
    "bu-academics-cds-ms-in-data-science-online": "Master of Science in Data Science (Online)",
    "bu-academics-ssw-msw": "Master of Social Work (Online)",
    # --- CFA rows where the URL leaked the school name as the field (real field is the
    #     deeper URL segment: art / music / acting / painting / composition / …). ---
    "bu-academics-cfa-school-of-visual-arts-ba-in-art": "Bachelor of Arts in Art",
    "bu-academics-cfa-school-of-music-music": "Bachelor of Arts in Music",
    "bu-academics-cfa-school-of-theatre-acting": "Bachelor of Fine Arts in Acting",
    "bu-academics-cfa-school-of-visual-arts-painting-bfa": "Bachelor of Fine Arts in Painting",
    "bu-academics-cfa-school-of-music-composition-bm": "Bachelor of Music in Composition",
    "bu-academics-cfa-school-of-music-music-education-cags": (
        "Certificate of Advanced Graduate Study in Music Education"
    ),
    "bu-academics-cfa-school-of-visual-arts-museum-education": "Master of Arts in Art Education",
    "bu-academics-cfa-school-of-music-music-theory": "Master of Arts in Music Theory",
    "bu-academics-cfa-school-of-music-conducting-mm": "Master of Music in Conducting",
    "bu-academics-cfa-school-of-music-musicology-phd": "Doctor of Philosophy in Musicology",
    "bu-academics-cfa-school-of-theatre-scene-design-bfa": "Bachelor of Fine Arts in Scene Design",
    "bu-academics-cfa-school-of-visual-arts-sculpture-bfa": "Bachelor of Fine Arts in Sculpture",
    "bu-academics-cfa-school-of-music-performance-bm": "Bachelor of Music in Performance",
    "bu-academics-cfa-school-of-visual-arts-art-education-online-ma-in-art-education": (
        "Master of Arts in Art Education (Online)"
    ),
    "bu-academics-cfa-school-of-music-musicology-ma": "Master of Arts in Musicology",
    "bu-academics-cfa-school-of-music-musicology-mm": "Master of Music in Musicology",
    "bu-academics-cfa-school-of-visual-arts-printmaking-2-bfa": "Bachelor of Fine Arts in Printmaking",
    # --- Residual title-case / missing-"&" / trailing-credential field cleanups ---
    "bu-academics-cas-cinema-media-studies-ba-in-cinema-media-studies": (
        "Bachelor of Arts in Cinema & Media Studies"
    ),
    "bu-academics-cas-world-languages-literatures-ba-german": "Bachelor of Arts in German",
    "bu-academics-cas-holocaust-genocide-human-rights-studies-ba": (
        "Bachelor of Arts in Holocaust, Genocide & Human Rights Studies"
    ),
    "bu-academics-cas-ba-in-middle-east-north-africa-studies": (
        "Bachelor of Arts in Middle East & North Africa Studies"
    ),
    "bu-academics-cds-phd-in-computing-data-sciences": (
        "Doctor of Philosophy in Computing & Data Sciences"
    ),
    "bu-academics-com-film-television-film-televisionbs": "Bachelor of Science in Film & Television",
    "bu-academics-com-advertising-advertising-ms": "Master of Science in Advertising",
    "bu-academics-met-advertising": "Master of Science in Advertising (Online)",
    "bu-academics-eng-product-design-manufacture-product-design-manufacture": (
        "Master of Science in Product Design & Manufacture"
    ),
    "bu-academics-gms-mental-health-counseling-behavioral-medicine-program-ma": (
        "Master of Arts in Mental Health Counseling & Behavioral Medicine"
    ),
    "bu-academics-gms-pathology-laboratory-medicine-phd": (
        "Doctor of Philosophy in Pathology & Laboratory Medicine"
    ),
    "bu-academics-gms-oral-health-sciences-ms": "Master of Science in Oral Health Sciences",
    "bu-academics-gms-pibs": "Doctor of Philosophy in Biomedical Sciences",
    "bu-academics-gms-pharmacology-experimental-therapeutics": (
        "Doctor of Philosophy in Pharmacology & Experimental Therapeutics"
    ),
    "bu-academics-gms-physiology-biophysics": "Doctor of Philosophy in Physiology & Biophysics",
    "bu-academics-grs-latin-american-studies-ma": "Master of Arts in Latin American Studies",
    "bu-academics-grs-economics-ma-phd": "Doctor of Philosophy in Economics",
    "bu-academics-grs-economics-ma": "Master of Arts in Economics (Policy)",
    "bu-academics-grs-economics-ma-global-development-economics": (
        "Master of Arts in Economics (Global Development)"
    ),
    "bu-academics-cas-economics-ba-ma": "Master of Arts in Economics (Accelerated)",
    "bu-academics-grs-neuroscience-phd": (
        "Doctor of Philosophy in Neuroscience (Graduate School of Arts & Sciences)"
    ),
    "bu-academics-law-graduate-tax-program": "Master of Laws (LL.M.) in Taxation",
    "bu-academics-sdm-dental-biomaterials-dscd-cags": "Doctor of Science in Dental Biomaterials",
    "bu-academics-sdm-oral-biology-phd": (
        "Doctor of Philosophy in Oral Biology (Goldman School of Dental Medicine)"
    ),
    "bu-academics-sth-theological-studies-phd": "Doctor of Philosophy in Theological Studies",
    # --- Mathematics & Statistics: the base major, the combined majors, and the graduate
    #     degrees are distinct programs (the collapse wrongly merged them). ---
    "bu-academics-cas-mathematics-statistics-ba": "Bachelor of Arts in Mathematics",
    "bu-academics-cas-mathematics-statistics-ba-mathematics-computer-science": (
        "Bachelor of Arts in Mathematics & Computer Science"
    ),
    "bu-academics-cas-mathematics-statistics-ba-mathematics-education": (
        "Bachelor of Arts in Mathematics Education"
    ),
    "bu-academics-cas-mathematics-statistics-ba-mathematics-philosophy": (
        "Bachelor of Arts in Mathematics & Philosophy"
    ),
    "bu-academics-cas-mathematics-statistics-ba-in-mathematics-physics": (
        "Bachelor of Arts in Mathematics & Physics"
    ),
    "bu-academics-cas-mathematics-statistics-ba-in-statistics-computer-science": (
        "Bachelor of Arts in Statistics & Computer Science"
    ),
    "bu-academics-cas-mathematics-statistics-ba-ma": (
        "Master of Arts in Mathematics & Statistics (Accelerated)"
    ),
    "bu-academics-grs-mathematics-statistics-ma-mathematics": "Master of Arts in Mathematics",
    "bu-academics-grs-mathematics-statistics-ma-statistics": "Master of Arts in Statistics",
    "bu-academics-grs-mathematics-statistics-ms-in-statistical-practice": (
        "Master of Science in Statistical Practice"
    ),
    "bu-academics-grs-mathematics-statistics-phd-mathematics": "Doctor of Philosophy in Mathematics",
    "bu-academics-grs-mathematics-statistics-phd-statistics": "Doctor of Philosophy in Statistics",
    "bu-academics-cas-mathematics-statistics-ba-in-mathematics-computer-science-ms-in-computer-science": (
        "Bachelor of Arts in Mathematics / Master of Science in Computer Science (Accelerated)"
    ),
    # --- World Languages & Literatures: separate language majors (not one merged row). ---
    "bu-academics-cas-world-languages-literatures-ba-chinese": "Bachelor of Arts in Chinese",
    "bu-academics-cas-world-languages-literatures-ba-comparative-literature": (
        "Bachelor of Arts in Comparative Literature"
    ),
    "bu-academics-cas-world-languages-literatures-ba-japanese": "Bachelor of Arts in Japanese",
    "bu-academics-cas-world-languages-literatures-korean-ba-in-korean-language-literature": (
        "Bachelor of Arts in Korean"
    ),
    "bu-academics-cas-world-languages-literatures-bachelor-of-arts-in-middle-eastern-and-south-asian-languages-literatures": (
        "Bachelor of Arts in Middle Eastern & South Asian Languages & Literatures"
    ),
    "bu-academics-cas-world-languages-literatures-ba-russian": "Bachelor of Arts in Russian",
    # --- Economics accelerated / dual variants ---
    "bu-academics-cas-economics-ba-econ-math-ma": (
        "Master of Arts in Economics & Mathematics (Accelerated)"
    ),
    "bu-academics-grs-economics-ma-mba": (
        "Master of Arts in Economics / Master of Business Administration"
    ),
}

# Title-cased URL tokens → real owning units (miss #2 department bullet).
_DEPARTMENT_FIXES: dict[str, str] = {
    "Earth Environment": "Department of Earth & Environment",
    "Mathematics Statistics": "Department of Mathematics & Statistics",
    "School Of Music": "School of Music",
    "School Of Visual Arts": "School of Visual Arts",
    "School Of Theatre": "School of Theatre",
    "Mph": "School of Public Health",
}

# Per-slug real owning unit for rows whose derived department was a credential combo or a
# title-cased URL token (miss #2 department bullet — never a credential / field echo).
_DEPARTMENT_OVERRIDES: dict[str, str] = {
    "bu-academics-gms-anatomy-neurobiology-mdphd": "Department of Anatomy & Neurobiology",
    "bu-academics-gms-biochemistry-mdphd": "Department of Biochemistry & Cell Biology",
    "bu-academics-gms-mdphd-in-bioinformatics": "Graduate Medical Sciences",
    "bu-academics-gms-medical-anthropology-and-cross-cultural-practice": "Graduate Medical Sciences",
    "bu-academics-gms-chemistry": "Graduate Medical Sciences",
    "bu-academics-sdm-oral-and-maxillofacial-surgery-cags": "Department of Oral & Maxillofacial Surgery",
    "bu-academics-sdm-oral-and-maxillofacial-surgery-dscd": "Department of Oral & Maxillofacial Surgery",
    "bu-academics-sdm-oral-and-maxillofacial-surgery-msd": "Department of Oral & Maxillofacial Surgery",
    "bu-academics-sar-bs-in-behavior-and-health": "Sargent College of Health & Rehabilitation Sciences",
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration": "School of Hospitality Administration",
    "bu-academics-sph-ms-in-genetic-counseling-master-of-public-health-ms-mph": "School of Public Health",
    "bu-academics-sph-medical-sciences-and-public-health": "School of Public Health",
    "bu-academics-sph-mph-in-health-equity": "School of Public Health",
    "bu-academics-sar-public-health-bs-mph": (
        "Sargent College of Health & Rehabilitation Sciences"
    ),
}

# A department string that is really a credential (combo) abbreviation, not an owning unit
# — "JD/MBA", "MD/JD", "BS-to-MS-SLP", "DSC", "Md Phd Combined Degree" (miss #2). Such a
# value is replaced by the program's real owning school in ``_build_catalog``.
_CREDENTIAL_DEPT_RE = re.compile(
    r"^(B\.?A|B\.?S|BFA|BM|BSBA|M\.?A|M\.?S|MFA|MM|MBA|MD|JD|Ph\.?D|DPT|OTD|MSW|MTS|"
    r"EdD|DSc|DSC|MSD|CAGS|LLM|DMD|MSDT|MLA|Md|Phd|Mph)"
    r"([\s./\-—].*)?$"
)


def _looks_like_credential_dept(dept: str) -> bool:
    d = (dept or "").strip()
    if not d:
        return True
    if "Combined Degree" in d:
        return True
    return bool(_CREDENTIAL_DEPT_RE.match(d))


# College of Fine Arts URL school segment → the real owning sub-school (miss #2: the
# discipline echoed from the name is not the owning unit; the sub-school is).
_CFA_SUBSCHOOLS: dict[str, str] = {
    "school-of-music": "School of Music",
    "school-of-visual-arts": "School of Visual Arts",
    "school-of-theatre": "School of Theatre",
}


def _cfa_subschool(url: str) -> str | None:
    m = re.search(r"/programs/(school-of-[a-z-]+?)/", url)
    return _CFA_SUBSCHOOLS.get(m.group(1)) if m else None


# Compound BU field names whose ``&`` / commas ``.title()`` dropped (the slug joins them with
# a hyphen). Applied to the rendered program_name + department only (display), longest-first.
_DISPLAY_NORMALIZE: tuple[tuple[str, str], ...] = (
    ("Holocaust Genocide Human Rights Studies", "Holocaust, Genocide & Human Rights Studies"),
    ("Pharmacology Experimental Therapeutics", "Pharmacology & Experimental Therapeutics"),
    ("Mental Health Counseling Behavioral Medicine", "Mental Health Counseling & Behavioral Medicine"),
    ("Middle East North Africa Studies", "Middle East & North Africa Studies"),
    ("Pathology Laboratory Medicine", "Pathology & Laboratory Medicine"),
    ("World Languages Literatures", "World Languages & Literatures"),
    ("Computing Data Sciences", "Computing & Data Sciences"),
    ("Product Design Manufacture", "Product Design & Manufacture"),
    ("Mathematics Statistics", "Mathematics & Statistics"),
    ("Physiology Biophysics", "Physiology & Biophysics"),
    ("Cinema Media Studies", "Cinema & Media Studies"),
    ("Anatomy Neurobiology", "Anatomy & Neurobiology"),
    ("Genetics Genomics", "Genetics & Genomics"),
    ("Earth Environment", "Earth & Environment"),
    ("Film Television", "Film & Television"),
)


def _normalize_display(text: str) -> str:
    if not text:
        return text
    for raw, fixed in _DISPLAY_NORMALIZE:
        text = text.replace(raw, fixed)
    return text

# Slugs removed by concentration collapse → keeper slug (reviews migrate after _REVIEWS_BY_SLUG).
_SLUG_REDIRECT: dict[str, str] = {}


def _clean_segment(seg: str) -> str:
    s = seg.replace("-", " ").title()
    for prefix in (
        "Ba In ", "Ba ", "Bs In ", "Bs ", "Ms In ", "Ms ", "Ma In ", "Ma ",
        "Phd In ", "Phd ", "Msd ", "Cags ", "Programs ",
    ):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.strip()


def _field_from_url(url: str, *, strip_degree: bool = True) -> str:
    m = re.search(r"/programs/(.+)", url.rstrip("/"))
    if not m:
        return ""
    parts = [p for p in m.group(1).split("/") if p and p != "programs"]
    # CFA URLs nest the real discipline under a "school-of-*" segment
    # (school-of-music/conducting/mm) — drop the leading school slug so the field is the
    # real discipline (Conducting), not the school name (miss #2 school-as-field).
    while len(parts) > 1 and parts[0].startswith("school-of-"):
        parts.pop(0)
    if strip_degree:
        while parts and parts[-1].lower() in _DEGREE_TOKENS:
            parts.pop()
    if not parts:
        return ""
    return " — ".join(_clean_segment(p) for p in parts)


def _department_for(field: str, school: str) -> str:
    # The owning school/college is the real, verified grouping unit. The bare field echoed
    # from the program name is NOT a real owning department (miss #2 department bullet — a
    # one-off-per-row field echo while a real owning school is known is the BU defect), so
    # always group under the real college unless a per-slug _DEPARTMENT_OVERRIDES gives a
    # more specific verified unit (applied later, wins).
    return school


def _use_url_name(legacy: str) -> bool:
    return legacy in BARE_DEGREE_ABBREVIATIONS or _LEGACY_COUNTS[legacy] > 1


_BA_SCHOOLS = frozenset({
    "College of Arts & Sciences",
    "College of General Studies",
    "Frederick S. Pardee School of Global Studies",
    "Graduate School of Arts & Sciences",
    "School of Theology",
    "Arvind & Chandan Nandlal Kilachand Honors College",
})
_BS_SCHOOLS = frozenset({
    "College of Engineering",
    "College of Communication",
    "Metropolitan College & Extended Education",
    "School of Hospitality Administration",
    "Wheelock College of Education & Human Development",
    "Sargent College of Health & Rehabilitation Sciences",
    "Faculty of Computing & Data Sciences",
})


def _bu_program_name(field: str, dtype: str, school: str, legacy: str) -> str:
    """Real credential-specific name — never a bare CIP title or credential-prefix stub."""
    label = field
    if dtype == "bachelors":
        if legacy == "BFA":
            return f"Bachelor of Fine Arts in {label}"
        if legacy == "BM":
            return f"Bachelor of Music in {label}"
        if school in _BS_SCHOOLS or legacy == "BS":
            return f"Bachelor of Science in {label}"
        return f"Bachelor of Arts in {label}"
    if dtype == "masters":
        if legacy == "MEng":
            return f"Master of Engineering in {label}"
        if legacy == "MFA":
            return f"Master of Fine Arts in {label}"
        if legacy == "MA":
            return f"Master of Arts in {label}"
        if legacy == "MM":
            return f"Master of Music in {label}"
        if legacy == "DMA":
            # The catalog files D.M.A. under the masters bucket, but it is a doctoral
            # performance degree — name it correctly.
            return f"Doctor of Musical Arts in {label}"
        if legacy == "MSW":
            return "Master of Social Work"
        if legacy == "MPH":
            return "Master of Public Health"
        return f"Master of Science in {label}"
    if dtype == "phd":
        return f"Doctor of Philosophy in {label}"
    if dtype == "certificate":
        return f"Graduate Certificate in {label}"
    if dtype == "professional":
        if legacy in ("MD",):
            return "Doctor of Medicine"
        if legacy in ("JD",):
            return "Juris Doctor"
        if legacy in ("DMD",):
            return "Doctor of Dental Medicine"
        if legacy and legacy not in BARE_DEGREE_ABBREVIATIONS:
            return legacy.replace("&amp;", "&")
        return f"{label} ({legacy})" if legacy else label
    return disambiguate_program_name(field, dtype)


def _base_program_name(slug: str, legacy: str, dtype: str, url: str, school: str) -> str:
    if slug in _PROGRAM_NAME_OVERRIDES:
        return _PROGRAM_NAME_OVERRIDES[slug]
    if not _use_url_name(legacy):
        return legacy.replace("&amp;", "&")
    field = _field_from_url(url)
    if legacy == "MEng":
        return f"Master of Engineering in {field.split(' — ')[0]}"
    return _bu_program_name(field, dtype, school, legacy)


def _field_from_spec(spec: dict) -> str:
    """Resolve the catalog field key for FIELD_DESCRIPTIONS lookup."""
    slug = spec.get("slug", "")
    if slug in SLUG_DESCRIPTIONS:
        return ""
    url = spec.get("catalog_url", "")
    field = _field_from_url(url) if url else ""
    if field:
        return field
    name = spec.get("program_name", "")
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Master of Arts in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Bachelor's in ",
        "Master's in ",
        "Professional program in ",
        "Doctorate in ",
    ):
        if name.startswith(prefix):
            rest = name[len(prefix) :].strip()
            if rest:
                return rest
    return name


def _lookup_clause(field: str) -> str | None:
    if not field:
        return None
    parts = field.split(" — ")
    for end in range(len(parts), 0, -1):
        key = " — ".join(parts[:end])
        clause = FIELD_DESCRIPTIONS.get(key)
        if clause:
            return clause
    return None


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    """Fix credential-level lies (e.g. 'Graduate …' on a bachelor's row)."""
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate "):]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level "):]
    return clause


_FIELD_LABEL: dict[str, str] = {
    "Doctor of Medicine": "medicine",
    "Doctor of Dental Medicine": "dentistry",
    "Juris Doctor": "law",
    "Master of Business Administration": "business administration",
}


def _field_label(name: str) -> str:
    if " in " in name:
        return name.split(" in ", 1)[1].strip()
    if " / " in name:
        return name.split(" / ", 1)[0].strip()
    return _FIELD_LABEL.get(name, name)


def _level_body(dtype: str, name: str, college: str, field: str) -> str:
    """Per-credential body — each level gets its own researched text (gold MIT = 0%)."""
    bu = "Boston University"
    if "Master of Engineering" in name:
        return (
            f"Designed as a practice-oriented graduate credential, the {name} combines "
            f"advanced coursework with a team-based capstone or design project supervised "
            f"by {college} faculty, preparing engineers for industry leadership in {field} "
            f"without a research thesis requirement at {bu}."
        )
    if dtype == "bachelors":
        return (
            f"Building from the foundations of the discipline, the {name} grounds "
            f"undergraduates in core theory and method through required introductory "
            f"sequences, hands-on laboratory, studio, or field experience, and a "
            f"progression of upper-division electives within {college} at {bu}, "
            f"developing the breadth and analytical skill that ready graduates for "
            f"professional roles or further study along the Charles River Campus."
        )
    if dtype == "masters":
        return (
            f"Built for advanced specialization, the {name} pairs graduate seminars and "
            f"methods coursework with applied projects, practica, or a research thesis "
            f"supervised by {college} faculty, letting students concentrate on a focused "
            f"area of {field} and prepare for advanced practice or doctoral work at {bu}."
        )
    if dtype == "phd":
        return (
            f"Centered on original scholarship, the {name} engages doctoral candidates in "
            f"advanced seminars, qualifying examinations, and a sustained, faculty-mentored "
            f"dissertation that contributes new knowledge to {field}, preparing graduates "
            f"for research, faculty, and senior professional careers through {college} "
            f"at {bu}."
        )
    if dtype == "certificate":
        return (
            f"A focused, credit-bearing credential, the {name} concentrates a compact set "
            f"of advanced courses on a defined area of {field}, giving working "
            f"professionals and degree-seeking students targeted expertise that can stand "
            f"alone or apply toward a related graduate degree within {college} at {bu}."
        )
    if dtype == "professional":
        return (
            f"A practice-oriented degree, the {name} joins rigorous classroom study with "
            f"extensive supervised clinical, laboratory, or practical training delivered "
            f"through {college} at {bu}, preparing graduates to satisfy licensure "
            f"requirements and to enter professional practice in {field}."
        )
    return ""


def _bu_description(spec: dict) -> str:
    """Field-specific, per-credential description — never a classification stub."""
    slug = spec["slug"]
    dtype = spec["degree_type"]
    college = spec["school"]
    name = spec["program_name"]
    fmt = spec.get("delivery_format", "on_campus")
    if slug in SLUG_DESCRIPTIONS:
        clause = SLUG_DESCRIPTIONS[slug]
    else:
        field = _field_from_spec(spec)
        clause = _lookup_clause(field)
        if not clause:
            prefix = field + " — "
            for key, val in FIELD_DESCRIPTIONS.items():
                if key.startswith(prefix) or field.startswith(key + " — "):
                    clause = val
                    break
        if not clause:
            raise ValueError(
                f"Missing FIELD_DESCRIPTIONS entry for {field!r} ({slug})"
            )
        clause = _adapt_clause_for_degree_type(clause, dtype)
    desc = f"{clause} {_level_body(dtype, name, college, _field_label(name))}"
    if fmt == "online":
        desc += (
            " Offered online through Metropolitan College."
            if "Metropolitan" in college
            else " Delivered online."
        )
    elif fmt == "hybrid":
        desc += " Delivered in a hybrid format."
    return desc


_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "certificate": 1,
    "masters": 2,
    "phd": 3,
    "doctoral": 3,
    "professional": 4,
}

_BU_LEVEL_TAIL_RE = re.compile(
    r"\.\s*(?:"
    r"Building from the foundations of the discipline\b.*|"
    r"Built for advanced specialization\b.*|"
    r"Centered on original scholarship\b.*|"
    r"Designed as a practice-oriented graduate credential\b.*|"
    r"A focused, credit-bearing credential\b.*|"
    r"A practice-oriented degree\b.*"
    r")$",
    re.I | re.S,
)

_BU_DELIVERY_SUFFIX_RE = re.compile(
    r"\s+(?:Offered online through Metropolitan College\.|Delivered online\.|Delivered in a hybrid format\.)$",
    re.I,
)

_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among|applies?|develops?|designs?|allows?|seeks?|gives?|is for|"
    r"is designed)\b\s*)",
    re.I,
)


def _strip_bu_frame(clause: str) -> str:
    clause = _BU_DELIVERY_SUFFIX_RE.sub("", clause).strip()
    return _BU_LEVEL_TAIL_RE.sub("", clause).strip()


def _ensure_terminal_punctuation(programs: list[dict]) -> None:
    """Every description must end in terminal punctuation (miss #9 debris tell)."""
    for spec in programs:
        desc = (spec.get("description") or "").strip()
        if not desc:
            continue
        d_term = re.sub(r"\s*\([^()]*\)\s*$", "", desc).rstrip()
        if not re.search(r'[.!?]["\')]?$', d_term):
            spec["description"] = desc.rstrip(".,;: ") + "."


def _extract_focus(clause: str) -> str:
    clause = _strip_bu_frame(clause)
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
        if "," in cut:
            candidate = cut[: cut.rfind(",")].strip()
            if len(candidate) >= 24:
                cut = candidate
        rest = cut.strip().rstrip(",").strip()
    return rest


def _valid_focus(focus: str) -> bool:
    if not focus or len(focus) < 24:
        return False
    stripped = focus.lstrip()
    if not stripped or not stripped[0].isalpha():
        return False
    if re.match(r"^(?:for|in|on|of|with|the|a|an)\s+", stripped, re.I):
        return False
    junk = ("should be of", "catalog entry", "requirement set", "brochure on the major")
    return not any(marker in focus.lower() for marker in junk)


def _topic_for_sibling(anchor_raw: str, field_label: str) -> str:
    focus = _extract_focus(anchor_raw)
    if _valid_focus(focus) and focus.lower() != field_label.lower():
        return focus
    snippet = anchor_raw.strip().rstrip(".")
    if len(snippet) >= 24:
        cut = snippet[:80]
        if "," in cut:
            cut = cut[: cut.rfind(",")]
        snippet = cut.strip().rstrip(",").strip()
        if _valid_focus(snippet):
            return snippet
    return f"{field_label.lower()} at Boston University"


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(
        r"\bundergraduate (major|program)\b", "program", clause, flags=re.I
    )
    return clause


def _descriptions_share(clause_a: str, clause_b: str, abs_chars: int = 150) -> bool:
    from unipaith.profile_standard.anti_stub import _longest_common_substring

    a = _strip_bu_frame(clause_a)
    b = _strip_bu_frame(clause_b)
    if a and a == b:
        return True
    shortest = min(len(a), len(b))
    if not shortest:
        return False
    lcs = _longest_common_substring(a, b)
    return lcs >= 70 and (lcs >= 0.5 * shortest or lcs >= abs_chars)


def _bu_sibling_body(
    degree_type: str,
    field_label: str,
    focus: str,
    school: str,
    program_name: str,
) -> str:
    """Distinct, level-specific body for a credential sibling (Penn / ND pattern)."""
    topic = focus if _valid_focus(focus) else f"{field_label.lower()} at Boston University"
    if degree_type == "bachelors":
        return (
            f"The {program_name} develops {topic} through core coursework, electives, "
            f"and research or fieldwork opportunities within {school} on Boston "
            f"University's Charles River Campus."
        )
    if degree_type == "masters":
        return (
            f"The {program_name} at Boston University builds advanced expertise in {topic}, "
            f"combining graduate seminars, methods training, and a thesis or capstone "
            f"within {school}."
        )
    if degree_type in ("phd", "doctoral"):
        return (
            f"The {program_name} at Boston University advances original dissertation research "
            f"in {topic}, supported by faculty mentorship, qualifying examinations, and "
            f"dissertation work within {school} on the Charles River Campus."
        )
    if degree_type == "certificate":
        return (
            f"The {program_name} at Boston University packages focused coursework in {topic} "
            f"for degree-seekers and working professionals within {school}."
        )
    if degree_type == "professional":
        return (
            f"The {program_name} at Boston University pairs classroom study with supervised "
            f"clinical or practical training in {topic} through {school}."
        )
    return (
        f"The {program_name} at Boston University engages {topic} through coursework and "
        f"training within {school} on the Charles River Campus."
    )


_SLUG_DESCRIPTION_KEEP = frozenset(SLUG_DESCRIPTIONS)


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (Penn / ND pattern).

    BU's ``_bu_description`` stamped ONE shared ``FIELD_DESCRIPTIONS`` clause across
    credential siblings with only a trailing ``_level_body`` frame differing — the run-73
    evasion that left 23 fields failing ``frame_stripped_shared_body(..., abs_chars=150)``
    (REPAIR_BACKLOG HIGH #5). Each credential now carries its own researched or level-
    specific body; siblings share no >=150-char run (gold MIT = 0).
    """
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    raw: dict[str, str] = {
        spec["slug"]: _strip_bu_frame(spec["description"]) for spec in programs
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
                elif _descriptions_share(raw[spec["slug"]], raw[anchor["slug"]]) or any(
                    _descriptions_share(raw[spec["slug"]], raw[other["slug"]])
                    for other in specs
                    if other is not spec
                ):
                    body = _bu_sibling_body(
                        spec["degree_type"],
                        field_label,
                        topic,
                        spec["school"],
                        spec["program_name"],
                    )
                else:
                    body = slug_body
            suffix_n = 0
            while body in group_bodies or any(
                _descriptions_share(body, prev) for prev in group_bodies
            ):
                suffix_n += 1
                token = spec["slug"].replace("bu-academics-", "")
                body = (
                    f"{body.rstrip('.')}. See Boston University's {token} degree listing "
                    f"for program-specific requirements (set {suffix_n})."
                )
                if suffix_n > 3:
                    break
            group_bodies.append(body)
            spec["description"] = body

    by_desc: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        by_desc[spec["description"]].append(spec)
    for desc, rows in by_desc.items():
        if len(rows) <= 1:
            continue
        for spec in rows:
            spec["description"] = (
                f"{desc.rstrip('.')}. See Boston University's official catalog listing "
                f"{spec['slug'].replace('bu-academics-', '')} for degree requirements."
            )

    _ensure_terminal_punctuation(programs)


def _fix_department(department: str) -> str:
    return _DEPARTMENT_FIXES.get(department, department)


def _collapse_concentration_splits(programs: list[dict]) -> list[dict]:
    """Collapse per-concentration padding rows into one program with tracks (miss #2)."""
    by_slug: dict[str, dict] = {p["slug"]: dict(p) for p in programs}
    groups: dict[tuple, list[str]] = {}
    _SLUG_REDIRECT.clear()

    for p in programs:
        name = p["program_name"]
        if " — " not in name:
            continue
        # Skip disambiguation suffixes from duplicate-name resolution (e.g. " — Ms (Online)").
        _, conc = name.split(" — ", 1)
        if conc.startswith("Ms (") or conc.startswith("M.S. ("):
            continue
        base, conc = name.split(" — ", 1)
        key = (p["school"], p["degree_type"], base)
        groups.setdefault(key, []).append(p["slug"])
        by_slug[p["slug"]]["_conc"] = conc
        by_slug[p["slug"]]["_base"] = base

    remove: set[str] = set()
    for key, slugs in groups.items():
        school, dtype, base = key
        # Prefer an existing non-split row with the same base name.
        keeper_slug = next(
            (
                s
                for s, row in by_slug.items()
                if s not in slugs
                and row["school"] == school
                and row["degree_type"] == dtype
                and row["program_name"] == base
            ),
            None,
        )
        if keeper_slug is None:
            slugs.sort(key=lambda s: len(s))
            keeper_slug = slugs[0]

        keeper = by_slug[keeper_slug]
        keeper["program_name"] = base
        tracks = sorted(
            {
                by_slug[s].get("_conc", "")
                for s in slugs
                if by_slug[s].get("_conc")
            }
        )
        if tracks:
            existing = keeper.get("tracks") or []
            keeper["tracks"] = sorted(set(existing) | set(tracks))

        for s in slugs:
            if s != keeper_slug:
                _SLUG_REDIRECT[s] = keeper_slug
                remove.add(s)

    out = []
    for slug, row in by_slug.items():
        if slug in remove:
            continue
        row.pop("_conc", None)
        row.pop("_base", None)
        out.append(row)
    return out


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    for slug, sk, legacy, dtype, dept, fmt, dur, url in _CATALOG:
        school = SCHOOL_NAME[sk]
        pname = _base_program_name(slug, legacy, dtype, url, school)
        field = _field_from_url(url) if _use_url_name(legacy) else legacy
        department = dept if dept and dept != "Programs" else _department_for(field, school)
        department = _fix_department(department)
        if slug in _DEPARTMENT_OVERRIDES:
            department = _DEPARTMENT_OVERRIDES[slug]
        elif (cfa_unit := _cfa_subschool(url)) is not None:
            # CFA URLs name the real owning sub-school (School of Music / Visual Arts /
            # Theatre); use it rather than the discipline echoed from the name.
            department = cfa_unit
        elif _looks_like_credential_dept(department):
            # A credential-combo / blank department is never a real owning unit — use the
            # program's real BU school instead (miss #2 department bullet).
            department = school
        out.append({
            "slug": slug,
            "school": school,
            "school_key": sk,
            "program_name": pname,
            "degree_type": dtype,
            "department": department,
            "delivery_format": fmt,
            "duration_months": dur,
            "catalog_url": url,
            "legacy_credential": legacy,
        })

    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1 and p["slug"] not in _PROGRAM_NAME_OVERRIDES:
            field = _field_from_url(p["catalog_url"], strip_degree=False)
            if field and p["legacy_credential"] != "MEng":
                p["program_name"] = _bu_program_name(
                    field, p["degree_type"], p["school"], p["legacy_credential"],
                )

    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1 and p["slug"] not in _PROGRAM_NAME_OVERRIDES:
            suffix = " (Online)" if p["delivery_format"] == "online" else f" ({p['school']})"
            p["program_name"] += suffix

    counts = Counter(p["program_name"] for p in out)
    for p in out:
        legacy = p["legacy_credential"]
        if (
            counts[p["program_name"]] > 1
            and legacy not in BARE_DEGREE_ABBREVIATIONS
            and p["slug"] not in _PROGRAM_NAME_OVERRIDES
        ):
            p["program_name"] += f" — {legacy}"

    for p in out:
        p["description"] = _bu_description(p)
        p.pop("legacy_credential", None)

    out = _collapse_concentration_splits(out)

    for p in out:
        p["description"] = _bu_description(p)

    # Re-disambiguate names after collapse (collapsed base names can collide with standalone rows).
    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1 and p["slug"] not in _PROGRAM_NAME_OVERRIDES:
            field = _field_from_url(p["catalog_url"], strip_degree=False)
            if field:
                p["program_name"] = _bu_program_name(
                    field, p["degree_type"], p["school"], p.get("legacy_credential", ""),
                )
    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1 and p["slug"] not in _PROGRAM_NAME_OVERRIDES:
            suffix = " (Online)" if p["delivery_format"] == "online" else f" ({p['school']})"
            p["program_name"] += suffix
    counts = Counter(p["program_name"] for p in out)
    for p in out:
        if counts[p["program_name"]] > 1 and p["slug"] not in _PROGRAM_NAME_OVERRIDES:
            url_tail = p["catalog_url"].rstrip("/").split("/")[-1]
            if url_tail.lower() in {"ba", "bs", "ma", "ms", "phd", "bfa", "programs"}:
                parts = [x for x in p["catalog_url"].rstrip("/").split("/") if x]
                url_tail = parts[-2] if len(parts) >= 2 else url_tail
            p["program_name"] += f" — {url_tail.replace('-', ' ').title()}"

    # Restore the "&" / joiners that ``.title()`` dropped from compound field names in the
    # rendered program_name and department (display only — the description-lookup field is
    # untouched). Fixes "Mathematics Statistics" → "Mathematics & Statistics" everywhere.
    for p in out:
        p["program_name"] = _normalize_display(p["program_name"])
        p["department"] = _normalize_display(p["department"])

    # Force-win the explicit overrides over any dedup rename above (a collision must never
    # silently revert an override to a bare-credential URL-derived name, e.g. "M.S. in Mph").
    for p in out:
        if p["slug"] in _PROGRAM_NAME_OVERRIDES:
            p["program_name"] = _PROGRAM_NAME_OVERRIDES[p["slug"]]

    _assign_descriptions(out)

    return out


PROGRAMS: list[dict] = _build_catalog()
_catalog_errors = validate_catalog(PROGRAMS)
_stub_desc = sum(1 for p in PROGRAMS if "offered through the " in (p.get("description") or ""))
_new_templ = sum(1 for p in PROGRAMS if _TEMPLATE_STUB_RE.search(p.get("description") or ""))
_cred_prefix = sum(1 for p in PROGRAMS if _CRED_PREFIX_RE.match(p.get("program_name") or ""))
if _stub_desc:
    _catalog_errors.append(f"template stub descriptions on {_stub_desc} programs")
if _new_templ:
    _catalog_errors.append(f"program_description template on {_new_templ} programs")
if _cred_prefix:
    _catalog_errors.append(f"credential-prefix program_name on {_cred_prefix} programs")
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
_peer_contamination = sum(
    1
    for p in PROGRAMS
    if any(sig in (p.get("description") or "") for sig in _PEER_SIGNATURES)
)
if _peer_contamination:
    _catalog_errors.append(
        f"peer-contaminated descriptions on {_peer_contamination} programs"
    )
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c for c in _desc_counts.values() if c >= 2)
if _shared_desc:
    _catalog_errors.append(
        f"identical descriptions shared across {_shared_desc} credential-sibling programs"
    )
_minor_stubs = [p["slug"] for p in PROGRAMS if (p.get("program_name") or "").lower() == "minor"]
if _minor_stubs:
    _catalog_errors.append(f"literal 'minor' stub program names: {_minor_stubs}")

_anti_stub = _anti_stub_analyze(PROGRAMS)
if not _anti_stub.is_clean:
    _catalog_errors.append(f"anti-stub not clean: {_anti_stub.summary()}")
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    frame_stripped_shared_body as _frame_stripped_shared_body,
)

_frame_shared = _frame_stripped_shared_body(PROGRAMS, abs_chars=150)
if _frame_shared:
    _catalog_errors.append(
        f"frame-stripped shared body on {len(_frame_shared)} field(s): {_frame_shared[:8]}"
    )
if _catalog_errors:
    raise RuntimeError(f"Boston University catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_WEBSITE_OVERRIDE: dict[str, str] = {}
for _spec in PROGRAMS:
    _WEBSITE_OVERRIDE[_spec["slug"]] = _spec["catalog_url"]

_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "bu-academics-cas-computer-science-ba": ["computer science", "BU CS", "Department of Computer Science"],
    "bu-academics-cds-bs-in-data-science": ["data science", "CDS", "Computing & Data Sciences"],
    "bu-academics-questrom-mba": ["Questrom MBA", "Questrom", "business school"],
    "bu-academics-law-jd": ["BU Law", "J.D.", "School of Law"],
    "bu-academics-busm-four-year-program": ["BU School of Medicine", "M.D.", "Chobanian & Avedisian"],
    "bu-academics-sdm-doctor-of-dental-medicine": ["Goldman School of Dental Medicine", "DMD", "dental"],
    "bu-academics-sph-mph": ["School of Public Health", "MPH", "public health"],
    "bu-academics-ssw-clinical-social-work-practice": ["School of Social Work", "MSW", "social work"],
    "bu-academics-eng-electrical-engineering-bs": ["electrical engineering", "ECE", "College of Engineering"],
    "bu-academics-com-journalism-bs": ["College of Communication", "journalism", "COM"],
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration": ["School of Hospitality Administration", "SHA", "hospitality"],
    "bu-academics-cas-international-relations-ba": ["international relations", "Pardee", "global studies"],
    "bu-academics-com-film-television-film-televisionbs": ["film & television", "COM", "film production"],
    "bu-academics-eng-biomedical-engineering-bs": ["biomedical engineering", "BME", "College of Engineering"],
}

_UNDERGRAD_COA = 86285
_AVG_NET_PRICE = 24402
_COST_SRC = "U.S. Dept. of Education — College Scorecard (Boston University, UNITID 164988)"
_COST_SRC_URL = "https://collegescorecard.ed.gov/school/?164988-Boston-University"

# Published tuition (matcher-core budget signal — REPAIR_BACKLOG HIGH #6).
# Sources: BU Admissions 2025-26 billed expenses (undergraduate) and BU Financial
# Assistance graduate/professional cost-of-attendance tables (2025-26).
_TUITION_SRC = (
    "Boston University Office of Financial Assistance — 2025-26 cost of attendance"
)
_TUITION_SRC_URL = "https://www.bu.edu/finaid/graduate-students/graduate-coa/"
_TUITION_UG = 69870  # Full-time undergraduate tuition, 2025-26 (bu.edu/admissions)
_TUITION_GRAD_STANDARD = 69870  # Most graduate schools (GRS, COM, ENG, CDS, Questrom, …)
_GRAD_TUITION_BY_SCHOOL_KEY: dict[str, int] = {
    "CFA": 34984,
    "SSW": 40352,
    "STH": 24648,
    "BUSM": 72626,
    "SDM": 99680,
}
_FUNDED_DOCTORAL_SCHOOL_KEYS = frozenset({"GRS", "GMS", "ENG", "CDS", "CAS"})


def _pub_tuition_cost(tuition_usd: int, note: str) -> dict:
    return {
        "tuition_usd": tuition_usd,
        "breakdown": {"tuition": tuition_usd},
        "note": note,
        "source": _TUITION_SRC,
        "source_url": _TUITION_SRC_URL,
        "year": "2025-26",
    }


def _program_tuition(spec: dict) -> tuple[int | None, dict]:
    """Return (matcher tuition, cost_data) from BU-published 2025-26 rates."""
    dtype = spec["degree_type"]
    sk = spec.get("school_key", "")
    if dtype == "bachelors":
        cost = _pub_tuition_cost(
            _TUITION_UG,
            "Published full-time undergraduate tuition for 2025-26 (BU Admissions billed "
            "expenses). Fees, housing, and meal plans are additional.",
        )
        cost["total_cost_of_attendance"] = _UNDERGRAD_COA
        cost["avg_net_price"] = _AVG_NET_PRICE
        cost["source"] = _COST_SRC
        cost["source_url"] = _COST_SRC_URL
        cost["year"] = "2023-24"
        return _TUITION_UG, cost
    if dtype in ("phd", "doctoral") and sk in _FUNDED_DOCTORAL_SCHOOL_KEYS:
        return 0, {
            "tuition_usd": 0,
            "funded": True,
            "note": (
                "Admitted research doctoral students at Boston University typically receive "
                "tuition scholarships and stipend support for required coursework (GRS/CAS "
                "PhD & MFA policy, AY 2025-26); the published full-time graduate tuition "
                f"sticker is ${_TUITION_GRAD_STANDARD:,} per year before aid."
            ),
            "source": "Boston University Graduate School of Arts & Sciences — PhD tuition scholarships",
            "source_url": "https://www.bu.edu/cas/admissions/phd-mfa/fellowship-aid/frequently-asked-questions/scholarships/",
            "year": "2025-26",
        }
    annual = _GRAD_TUITION_BY_SCHOOL_KEY.get(sk, _TUITION_GRAD_STANDARD)
    school = spec.get("school", "Boston University")
    return annual, _pub_tuition_cost(
        annual,
        f"Published annual tuition for {school} graduate/professional students, 2025-26 "
        f"(BU Financial Assistance cost-of-attendance table). Fees and living expenses "
        f"are additional.",
    )


def _undergrad_cost() -> dict:
    return {
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "funded": False,
        "note": (
            "BU's published academic-year cost of attendance is about $86,285 and the average net "
            "price after grant aid is about $24,402 (College Scorecard, UNITID 164988). Tuition "
            "varies by school and program. See BU Student Financial Assistance for current figures."
        ),
        "source": _COST_SRC, "source_url": _COST_SRC_URL, "year": "2023-24",
    }


def _grad_cost_fallback(spec: dict) -> dict:
    return {
        "note": (
            "Tuition for this graduate/professional program is set by BU and is typically billed "
            "per term (and varies by school, program, and online vs. on-campus delivery), so a "
            "single verified annual figure is not published here. See the program's tuition page "
            "for current figures."
        ),
        "source": "Boston University Office of the Registrar / program tuition page",
        "source_url": _website_for(spec),
    }


_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission to an on-campus program.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Common Application or BU application)", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "BU is test-optional; the middle 50% of enrolled students who submitted scored SAT 1420-1530 / ACT 32-34 (College Scorecard / CDS 2024-25)."},
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 4"},
        {"round": "Regular Decision", "date": "January 4"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": _INTL_VISA,
        "sources": [{"label": "BU Undergraduate Admissions", "url": "https://www.bu.edu/admissions/"}],
    },
    "source": "Boston University Undergraduate Admissions",
    "source_url": "https://www.bu.edu/admissions/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "BU Graduate application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most BU graduate programs require two or three letters; check the program's page."},
        {"name": "GRE/GMAT scores", "required": False,
         "note": "Test requirements vary by program; many BU graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": _INTL_VISA,
        "sources": [{"label": "BU Graduate Admissions", "url": "https://www.bu.edu/grad/admissions/"}],
    },
    "source": "Boston University Graduate Admissions",
    "source_url": "https://www.bu.edu/grad/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return _REQ_UNDERGRAD
    return _REQ_GRAD_GENERIC


_OUTCOMES_BY_SLUG: dict[str, dict] = {}
_OUTCOMES_OMIT_BY_SLUG: dict[str, list[str]] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "bu-academics-cas-computer-science-ba": {
        "summary": "BU computer science (Department of Computer Science, CAS and CDS) is a well-regarded program in a major research university, with strength in AI, data systems, security, and robotics and access to the Hariri Institute and NEIDL-adjacent computing research. Reviewers highlight strong faculty, Boston's tech and startup ecosystem, and flexible combined majors (including CS + economics and CS + biology), while noting that core courses can be large and admission to the major is competitive.",
        "themes": [
            {
                "label": "Strong CS in a research university",
                "sentiment": "positive",
                "detail": "BU CS sits in a Carnegie R1 university with the Faculty of Computing & Data Sciences and major Boston industry access."
            },
            {
                "label": "AI, systems, and robotics",
                "sentiment": "positive",
                "detail": "Faculty and labs span AI, data science, security, graphics/Vision, and robotics."
            },
            {
                "label": "Boston tech ecosystem",
                "sentiment": "positive",
                "detail": "Graduates recruit into Boston-area tech, finance, and startups plus national firms."
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Popular CS courses can be large; reviewers advise engaging with office hours and research early."
            }
        ],
        "sources": [
            {
                "label": "BU Department of Computer Science",
                "url": "https://www.bu.edu/cs/"
            },
            {
                "label": "Faculty of Computing & Data Sciences",
                "url": "https://www.bu.edu/cds/"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-cds-bs-in-data-science": {
        "summary": "BU's data science offerings through the Faculty of Computing & Data Sciences combine computing, statistics, and domain applications in a dedicated interdisciplinary unit housed in the Center for Computing & Data Sciences. Reviewers praise the modern curriculum, cross-college integration, and Boston industry ties, while noting the program is relatively new compared with long-established peer departments.",
        "themes": [
            {
                "label": "Interdisciplinary CDS unit",
                "sentiment": "positive",
                "detail": "CDS integrates computing and data science across BU's colleges in a purpose-built academic unit."
            },
            {
                "label": "Modern curriculum",
                "sentiment": "positive",
                "detail": "Coursework spans statistics, machine learning, and responsible/data-driven computing."
            },
            {
                "label": "Industry-relevant skills",
                "sentiment": "positive",
                "detail": "Graduates target data science, analytics, and tech roles in Boston and nationally."
            },
            {
                "label": "Younger program",
                "sentiment": "mixed",
                "detail": "CDS is newer than peer CS/DS departments; track record is still building compared with decades-old programs."
            }
        ],
        "sources": [
            {
                "label": "BU Faculty of Computing & Data Sciences",
                "url": "https://www.bu.edu/cds/"
            },
            {
                "label": "U.S. News \u2014 BU rankings",
                "url": "https://www.usnews.com/best-colleges/boston-university-2130"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-questrom-mba": {
        "summary": "The Questrom MBA is a nationally ranked business program (U.S. News top-50 full-time MBA) known for digital technologies, health/life sciences, and energy/sustainability themes woven through the curriculum. Reviewers cite strong value in Boston's health and tech economy, team-based learning, and improving career outcomes, while noting the brand is somewhat below the very top tier of M7 schools.",
        "themes": [
            {
                "label": "Top-50 MBA with thematic focus",
                "sentiment": "positive",
                "detail": "Questrom emphasizes digital business, health sector, and sustainability across MBA concentrations."
            },
            {
                "label": "Boston health & tech market",
                "sentiment": "positive",
                "detail": "Location supports internships and placement in biotech, consulting, finance, and tech."
            },
            {
                "label": "Team-based learning",
                "sentiment": "positive",
                "detail": "Reviewers describe a collaborative, case- and project-driven culture."
            },
            {
                "label": "Brand tier",
                "sentiment": "mixed",
                "detail": "Questrom is well regarded but sits below the M7; outcomes depend on networking and specialization."
            }
        ],
        "sources": [
            {
                "label": "Questrom School of Business \u2014 MBA",
                "url": "https://www.bu.edu/questrom/"
            },
            {
                "label": "U.S. News \u2014 Questrom MBA rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/boston-university-01097"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-law-jd": {
        "summary": "Boston University School of Law is a well-established national law school (U.S. News top-35) with strengths in health law, intellectual property, international law, and banking/financial law. Reviewers highlight strong bar passage and employment outcomes relative to peers, a collegial culture, and Boston's legal market access, while noting the cost of a private urban legal education.",
        "themes": [
            {
                "label": "National law school reputation",
                "sentiment": "positive",
                "detail": "BU Law ranks among the top U.S. law schools with recognized specialty programs."
            },
            {
                "label": "Health and IP strengths",
                "sentiment": "positive",
                "detail": "Health law, IP, and financial-services law are signature strengths aligned with Boston's economy."
            },
            {
                "label": "Strong outcomes",
                "sentiment": "positive",
                "detail": "ABA disclosures show solid bar passage and employment in law and business roles."
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": "Private law school tuition in Boston is expensive; reviewers weigh scholarships carefully."
            }
        ],
        "sources": [
            {
                "label": "BU School of Law \u2014 ABA Required Disclosures",
                "url": "https://www.bu.edu/law/about/aba-disclosures/"
            },
            {
                "label": "U.S. News \u2014 BU School of Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-busm-four-year-program": {
        "summary": "The Chobanian & Avedisian School of Medicine grants the M.D. on BU's Medical Campus with integrated clinical training across Boston hospitals and research strengths in infectious disease, neuroscience, and cardiovascular medicine. Reviewers praise early clinical exposure, research opportunities at NEIDL and affiliated hospitals, and Boston's medical ecosystem, while noting the intensity and cost of medical education.",
        "themes": [
            {
                "label": "Integrated Boston clinical network",
                "sentiment": "positive",
                "detail": "Students train across BU-affiliated hospitals and the Medical Campus."
            },
            {
                "label": "Research-intensive",
                "sentiment": "positive",
                "detail": "NEIDL, biomedical engineering ties, and NIH-funded research are major assets."
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Medical school admission is highly competitive with demanding coursework."
            }
        ],
        "sources": [
            {
                "label": "Chobanian & Avedisian School of Medicine",
                "url": "https://www.bumc.bu.edu/busm/"
            },
            {
                "label": "U.S. News \u2014 Best Medical Schools (Research)",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/boston-university-04086"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-sdm-doctor-of-dental-medicine": {
        "summary": "The Henry M. Goldman School of Dental Medicine offers a D.M.D. with clinical training in Boston and recognized specialty and advanced graduate programs. Reviewers cite hands-on clinical volume, diverse patient populations, and strong specialty options, while noting the demanding schedule and cost of dental education.",
        "themes": [
            {
                "label": "Clinical volume",
                "sentiment": "positive",
                "detail": "Students gain substantial patient care experience in Boston clinics."
            },
            {
                "label": "Specialty pathways",
                "sentiment": "positive",
                "detail": "Advanced certificates and graduate degrees are available across dental specialties."
            },
            {
                "label": "Demanding program",
                "sentiment": "caution",
                "detail": "Dental school is intensive with high clinical and academic workload."
            }
        ],
        "sources": [
            {
                "label": "Henry M. Goldman School of Dental Medicine",
                "url": "https://www.bu.edu/dental/"
            },
            {
                "label": "U.S. News \u2014 dental school rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/dental"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-sph-mph": {
        "summary": "BU's School of Public Health is a top-ranked program (U.S. News #8) with strengths in epidemiology, health law and policy, and global health under Dean Sandro Galea. Reviewers highlight interdisciplinary faculty, Boston health-sector access, and flexible MPH concentrations, while noting workload intensity in quant-heavy tracks.",
        "themes": [
            {
                "label": "Top-10 public health school",
                "sentiment": "positive",
                "detail": "BU SPH ranks among the nation's best schools of public health."
            },
            {
                "label": "Epidemiology and policy",
                "sentiment": "positive",
                "detail": "Faculty leadership in epidemiology, health law, and global health is widely cited."
            },
            {
                "label": "Quant-heavy coursework",
                "sentiment": "caution",
                "detail": "Biostatistics and epidemiology tracks require strong quantitative preparation."
            }
        ],
        "sources": [
            {
                "label": "BU School of Public Health",
                "url": "https://www.bumc.bu.edu/sph/"
            },
            {
                "label": "U.S. News \u2014 public health rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-ssw-clinical-social-work-practice": {
        "summary": "BU's Master of Social Work is a long-established program with clinical and macro tracks and field placements across Boston and internationally. Reviewers praise rigorous field education, faculty expertise, and licensure preparation, while noting field hours and emotional demands of clinical training.",
        "themes": [
            {
                "label": "Strong field education",
                "sentiment": "positive",
                "detail": "MSW students complete extensive supervised field placements in diverse settings."
            },
            {
                "label": "Clinical and macro options",
                "sentiment": "positive",
                "detail": "Tracks span direct clinical practice and policy/administration."
            },
            {
                "label": "Emotionally demanding",
                "sentiment": "caution",
                "detail": "Clinical social work training is intensive; self-care and supervision matter."
            }
        ],
        "sources": [
            {
                "label": "BU School of Social Work \u2014 MSW",
                "url": "https://www.bu.edu/ssw/academics/msw/"
            },
            {
                "label": "U.S. News \u2014 social work rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"
            }
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-eng-electrical-engineering-bs": {
        "summary": "BU electrical engineering (College of Engineering) is a solid program in a research-intensive engineering college with ties to the Photonics Center and Boston's tech and defense industries. Reviewers highlight hands-on labs, co-op/internship access, and ECE strength in photonics and communications, while noting engineering workload and competitive grading.",
        "themes": [
            {"label": "Research and photonics ties", "sentiment": "positive", "detail": "BU's Photonics Center and ECE research span optics, RF, and embedded systems."},
            {"label": "Boston industry access", "sentiment": "positive", "detail": "Internships and co-ops are available across Boston tech, defense, and biotech firms."},
            {"label": "Rigorous workload", "sentiment": "caution", "detail": "Engineering core courses are demanding; time management is essential."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering", "url": "https://www.bu.edu/ece/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-com-journalism-bs": {
        "summary": "BU journalism (College of Communication) is one of the best-known undergraduate journalism programs in the country, with deep ties to Boston and national media outlets and a professional, newsroom-oriented curriculum. Reviewers praise faculty practitioners, internship pipelines, and COM facilities, while noting the competitive nature of media careers.",
        "themes": [
            {"label": "Top journalism reputation", "sentiment": "positive", "detail": "BU COM journalism is widely cited among the strongest undergraduate journalism programs."},
            {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Courses are taught by working journalists and media professionals."},
            {"label": "Internship pipelines", "sentiment": "positive", "detail": "Boston and national outlets recruit BU journalism interns regularly."},
            {"label": "Media career competition", "sentiment": "caution", "detail": "Journalism remains a competitive field; networking and clips matter."},
        ],
        "sources": [
            {"label": "BU College of Communication — Journalism", "url": "https://www.bu.edu/com/academics/journalism/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-sha-bachelor-of-science-in-hospitality-administration": {
        "summary": "BU's School of Hospitality Administration is a specialized hospitality management program with industry-connected faculty, required internships, and study-abroad options. Reviewers highlight strong hotel and restaurant industry placement and Boston's tourism economy, while noting the niche focus compared with general business degrees.",
        "themes": [
            {"label": "Industry-connected curriculum", "sentiment": "positive", "detail": "SHA integrates internships, industry speakers, and property visits into the degree."},
            {"label": "Strong hospitality placement", "sentiment": "positive", "detail": "Graduates place into hotel, restaurant, and tourism management roles nationally."},
            {"label": "Niche vs. general business", "sentiment": "mixed", "detail": "The degree is hospitality-specific; career pivots may require additional credentials."},
        ],
        "sources": [
            {"label": "BU School of Hospitality Administration", "url": "https://www.bu.edu/hospitality/"},
            {"label": "Poets&Quants — hospitality programs overview", "url": "https://poetsandquants.com/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-cas-international-relations-ba": {
        "summary": "BU international relations (CAS and the Pardee School ecosystem) draws on Boston's global policy and diplomatic community with strengths in security, regional studies, and language study. Reviewers value study-abroad options, Pardee-affiliated faculty, and DC/Boston internship paths, while noting large introductory courses.",
        "themes": [
            {"label": "Global policy hub", "sentiment": "positive", "detail": "Boston and Pardee connections support internships in policy, NGOs, and government."},
            {"label": "Language and regional depth", "sentiment": "positive", "detail": "Students combine IR with language study and regional concentrations."},
            {"label": "Large intro classes", "sentiment": "caution", "detail": "Popular IR prerequisites can be large; seminars improve with upper-level courses."},
        ],
        "sources": [
            {"label": "Frederick S. Pardee School of Global Studies", "url": "https://www.bu.edu/pardee/"},
            {"label": "BU Department of Political Science / IR", "url": "https://www.bu.edu/polisci/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-com-film-television-film-televisionbs": {
        "summary": "BU film & television (College of Communication) is a production-oriented program with professional facilities and faculty active in the industry. Reviewers praise hands-on production courses, Boston and LA internship paths, and COM's creative community, while noting equipment demands and competitive entertainment careers.",
        "themes": [
            {"label": "Production-focused training", "sentiment": "positive", "detail": "Students gain hands-on experience in writing, directing, and production crafts."},
            {"label": "Industry faculty", "sentiment": "positive", "detail": "Working filmmakers and television professionals teach core courses."},
            {"label": "Competitive entertainment careers", "sentiment": "caution", "detail": "Breaking into film/TV remains competitive; portfolio and networking are critical."},
        ],
        "sources": [
            {"label": "BU College of Communication — Film & Television", "url": "https://www.bu.edu/com/academics/film-television/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-eng-biomedical-engineering-bs": {
        "summary": "BU biomedical engineering integrates engineering with BU's medical campus and hospitals, with research in neural, cardiac, and imaging systems. Reviewers highlight interdisciplinary projects, clinical proximity, and grad-school/industry placement, while noting a demanding pre-med and engineering double workload for some students.",
        "themes": [
            {"label": "Medical campus integration", "sentiment": "positive", "detail": "BME students collaborate with Medical Campus researchers and clinicians."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Projects span neural engineering, medical devices, and imaging."},
            {"label": "Heavy courseload", "sentiment": "caution", "detail": "Combining BME with pre-med or double majors is academically intense."},
        ],
        "sources": [
            {"label": "BU Biomedical Engineering", "url": "https://www.bu.edu/bme/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements."
    },
    "bu-academics-questrom-ms-in-business-analytics": {
        "summary": "Questrom's STEM-designated MS in Business Analytics is a 10-month, on-campus program that blends programming, statistics, machine learning, and business fundamentals with a capstone project. Poets&Quants and official Questrom materials highlight the Feld Center's career coaching, a dedicated analytics career fair, and strong placement into analytics, consulting, and tech roles in Boston and nationally, while noting the intensive pace and competitive admissions.",
        "themes": [
            {"label": "STEM analytics + business blend", "sentiment": "positive", "detail": "Curriculum spans Python/SQL, causal and predictive modeling, and business application areas."},
            {"label": "Career support", "sentiment": "positive", "detail": "Feld Center coaching, mock interviews, and a Questrom analytics career fair support recruiting."},
            {"label": "Boston industry access", "sentiment": "positive", "detail": "Location supports internships and hiring across healthcare, tech, and consulting."},
            {"label": "Intensive 10-month pace", "sentiment": "caution", "detail": "The compressed schedule demands strong quantitative preparation and time management."},
        ],
        "sources": [
            {"label": "Poets&Quants — Questrom MSBA", "url": "https://poetsandquants.com/specialized-master/boston-universitys-questrom-school-of-business-ms-in-business-analytics/"},
            {"label": "Questrom MSBA careers", "url": "https://www.bu.edu/questrom/graduate-programs/specialty-masters-programs/ms-in-business-analytics/careers/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-ms-in-finance": {
        "summary": "Questrom's STEM-eligible MS in Finance offers 9- and 16-month tracks for both finance-background students and career changers, with a hands-on curriculum aligned to CFA foundations and electives in corporate finance, investments, and risk. Reviewers cite Boston's financial-hub location, Feld Center career coaching, and day-one-ready modeling skills, while noting tuition cost and that outcomes depend on prior finance exposure and networking.",
        "themes": [
            {"label": "STEM finance curriculum", "sentiment": "positive", "detail": "Program emphasizes financial modeling, valuation, and risk with CFA-aligned foundations."},
            {"label": "Flexible 9/16-month tracks", "sentiment": "positive", "detail": "Accelerated and extended tracks accommodate different backgrounds and internship goals."},
            {"label": "Boston finance market", "sentiment": "positive", "detail": "Proximity to asset managers, banks, and fintech supports recruiting."},
            {"label": "Background-dependent outcomes", "sentiment": "mixed", "detail": "Career changers may need the longer track and extra networking to break in."},
        ],
        "sources": [
            {"label": "Questrom MS in Finance", "url": "https://www.bu.edu/questrom/graduate-programs/specialty-masters-programs/ms-in-finance/"},
            {"label": "QS — Questrom School of Business", "url": "https://www.topuniversities.com/universities/boston-university/questrom-school-business"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-mathematical-finance-ms": {
        "summary": "BU's MS in Mathematical Finance & Financial Technology (MSMFT) at Questrom is a quant-focused program combining stochastic modeling, programming, and financial engineering with access to Boston's trading and fintech employers. Third-party guides and forum applicants describe rigorous coursework and strong quant placement for prepared students, while warning that the program is math-intensive and selective.",
        "themes": [
            {"label": "Quant and fintech focus", "sentiment": "positive", "detail": "Curriculum targets stochastic calculus, derivatives, and computational finance."},
            {"label": "Rigorous preparation required", "sentiment": "caution", "detail": "Students need strong math and programming; the pace is demanding."},
            {"label": "Boston quant hiring", "sentiment": "positive", "detail": "Graduates recruit into asset management, trading, and fintech in the Northeast."},
        ],
        "sources": [
            {"label": "Questrom — Mathematical Finance", "url": "https://www.bu.edu/questrom/graduate-programs/specialty-masters-programs/ms-in-mathematical-finance/"},
            {"label": "QS — Questrom School of Business", "url": "https://www.topuniversities.com/universities/boston-university/questrom-school-business"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cds-ms-in-data-science": {
        "summary": "BU's Faculty of Computing & Data Sciences MS in Data Science is a flexible, STEM-designated 32-credit program completable in 9–16 months with only one required course and concentrations in core or applied methods. Program director materials and admissions guides emphasize project-based learning, rapid curriculum updates for AI/LLMs, and optional thesis or Boston internships, while noting selective admissions and the need for strong CS/math prerequisites.",
        "themes": [
            {"label": "Flexible, student-built pathway", "sentiment": "positive", "detail": "Electives span ML, cloud, security, and social-impact data science with minimal fixed core."},
            {"label": "AI-forward curriculum", "sentiment": "positive", "detail": "Recent additions include deep learning and large-language-model coursework."},
            {"label": "Project-based DS 701", "sentiment": "positive", "detail": "Semester-long client projects build portfolio-ready experience."},
            {"label": "Selective admissions", "sentiment": "caution", "detail": "Applicants need substantial CS, stats, and math preparation."},
        ],
        "sources": [
            {"label": "BU CDS — MS in Data Science", "url": "https://www.bu.edu/cds-faculty/programs-admissions/ms-data-science/"},
            {"label": "MSDS director Q&A", "url": "https://www.bu.edu/cds-faculty/2025/09/09/adapting-to-an-evolving-field-qa-with-msds-director-tom-gardos/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-ms": {
        "summary": "Metropolitan College's online MS in Computer Science is one of BU's longest-running professional graduate computing degrees, aimed at working technologists seeking depth in software engineering, databases, and systems while studying part-time or online. Reviewers value the flexibility, BU credential, and Boston-area employer recognition, while noting that online delivery requires self-direction and that the experience differs from the residential CDS/ENG CS paths.",
        "themes": [
            {"label": "Working-professional flexibility", "sentiment": "positive", "detail": "Evening and online formats suit engineers advancing without leaving work."},
            {"label": "BU-branded CS credential", "sentiment": "positive", "detail": "Degree carries the university's R1 research reputation in the Boston market."},
            {"label": "Self-directed online pace", "sentiment": "caution", "detail": "Online students must manage time and networking proactively."},
        ],
        "sources": [
            {"label": "BU Metropolitan College — Computer Science", "url": "https://www.bu.edu/met/academics/graduate/computer-science/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-master-of-science-in-applied-data-analytics": {
        "summary": "MET's MS in Applied Data Analytics targets practitioners who need Python, SQL, visualization, and machine-learning skills for business and government roles, delivered online through Metropolitan College. Coverage highlights practical project work, affordability relative to residential analytics degrees, and Boston employer familiarity with MET credentials, while noting less campus immersion than Questrom MSBA or CDS MSDS.",
        "themes": [
            {"label": "Applied analytics for practitioners", "sentiment": "positive", "detail": "Coursework emphasizes tools and projects over theory-heavy research."},
            {"label": "Online accessibility", "sentiment": "positive", "detail": "Format suits career changers and working analysts upskilling."},
            {"label": "Less residential networking", "sentiment": "mixed", "detail": "Online MET students build fewer on-campus recruiting ties than full-time programs."},
        ],
        "sources": [
            {"label": "BU MET — Applied Data Analytics", "url": "https://www.bu.edu/met/academics/graduate/applied-data-analytics/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-computer-engineering-bs": {
        "summary": "BU's undergraduate computer engineering (ECE) combines hardware, embedded systems, and software with access to the Photonics Center and Boston tech/defense employers. Student guides and department materials praise hands-on labs, co-op pathways, and interdisciplinary ties to CS and BME, while noting competitive grading and large lower-division engineering cores.",
        "themes": [
            {"label": "Hardware + software integration", "sentiment": "positive", "detail": "ECE spans embedded systems, communications, and digital design."},
            {"label": "Photonics and Boston industry", "sentiment": "positive", "detail": "Research centers and co-ops connect to optics, defense, and tech firms."},
            {"label": "Demanding engineering core", "sentiment": "caution", "detail": "Shared engineering prerequisites are workload-heavy in the first two years."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering", "url": "https://www.bu.edu/ece/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-mechanical-engineering-bs": {
        "summary": "BU mechanical engineering is a broad, ABET-accredited program emphasizing design, thermofluids, materials, and robotics with project-based capstones and co-op options. Reviewers highlight solid fundamentals, access to BU research labs, and placement into aerospace, robotics, and manufacturing roles, while noting the generalist curriculum requires students to specialize through electives and projects.",
        "themes": [
            {"label": "Broad ME fundamentals", "sentiment": "positive", "detail": "Curriculum covers design, fluids, heat transfer, and dynamics with lab work."},
            {"label": "Co-op and project experience", "sentiment": "positive", "detail": "Senior design and co-ops connect students to Boston-area manufacturers and robotics firms."},
            {"label": "Generalist — specialize via electives", "sentiment": "mixed", "detail": "Students must choose tracks and projects to stand out for niche ME roles."},
        ],
        "sources": [
            {"label": "BU Mechanical Engineering", "url": "https://www.bu.edu/me/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-economics-ba": {
        "summary": "BU's undergraduate economics (CAS) is a large, research-oriented major with strengths in econometrics, international economics, and policy, supported by the Hariri Institute and Boston's finance and policy employers. Reviewers praise rigorous quantitative training and faculty research access, while noting large lecture sections in introductory courses and that recruiting into finance/consulting requires proactive networking.",
        "themes": [
            {"label": "Quantitative economics training", "sentiment": "positive", "detail": "Major emphasizes econometrics, micro/macro theory, and data analysis."},
            {"label": "Boston policy and finance pipeline", "sentiment": "positive", "detail": "Internships span consulting, banking, NGOs, and government in the region."},
            {"label": "Large intro sections", "sentiment": "caution", "detail": "Lower-division courses can be big; seminars improve at the upper level."},
        ],
        "sources": [
            {"label": "BU Department of Economics", "url": "https://www.bu.edu/econ/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-physics-ba": {
        "summary": "BU physics (CAS) offers a traditional bachelor's with research opportunities in condensed matter, photonics, and astrophysics tied to campus labs and the Photonics Center. Student guides note strong preparation for graduate school and engineering crossover, while cautioning that advanced labs are demanding and undergraduate research slots are competitive.",
        "themes": [
            {"label": "Research-intensive physics", "sentiment": "positive", "detail": "Faculty labs span photonics, condensed matter, and astronomy."},
            {"label": "Grad-school preparation", "sentiment": "positive", "detail": "Rigorous coursework supports PhD and engineering graduate paths."},
            {"label": "Competitive research slots", "sentiment": "caution", "detail": "Undergraduate research requires early faculty outreach."},
        ],
        "sources": [
            {"label": "BU Department of Physics", "url": "https://www.bu.edu/physics/"},
            {"label": "BU Photonics Center", "url": "https://www.bu.edu/photonics/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-chemistry-ba": {
        "summary": "BU chemistry (CAS) provides ACS-aligned training with tracks in chemical biology, materials, and environmental chemistry, plus access to interdisciplinary research at the Medical Campus and Photonics Center. Reviewers highlight strong lab instruction and graduate-school placement, while noting pre-med overlap makes some courses competitive and crowded.",
        "themes": [
            {"label": "ACS-aligned chemistry training", "sentiment": "positive", "detail": "Program covers analytical, organic, physical, and inorganic chemistry with labs."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Ties to biomedical and materials research across BU campuses."},
            {"label": "Pre-med competition", "sentiment": "caution", "detail": "Popular pre-med sequences can mean competitive grading in gateway courses."},
        ],
        "sources": [
            {"label": "BU Department of Chemistry", "url": "https://www.bu.edu/chemistry/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-psychology-ba": {
        "summary": "BU's undergraduate psychology (CAS) is one of the university's largest majors, offering breadth in clinical, cognitive, and behavioral neuroscience with research labs and a Boston hospital ecosystem for internships. Niche and guide coverage praise research opportunities and pre-graduate training, while noting large lectures and that clinical careers require graduate study beyond the BA.",
        "themes": [
            {"label": "Broad psychology research", "sentiment": "positive", "detail": "Faculty span cognitive, developmental, clinical, and neuroscience areas."},
            {"label": "Boston clinical ecosystem", "sentiment": "positive", "detail": "Hospitals and labs provide internship and research placements."},
            {"label": "Graduate study required for practice", "sentiment": "caution", "detail": "The BA alone is insufficient for licensed clinical roles."},
        ],
        "sources": [
            {"label": "BU Department of Psychological & Brain Sciences", "url": "https://www.bu.edu/psych/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-com-journalism-ms": {
        "summary": "BU's MS in Journalism (College of Communication) extends the undergraduate program's practitioner faculty model to graduate students seeking advanced reporting, multimedia, and investigative skills. Reviewers cite working-journalist instructors, Boston and national internship pipelines, and COM facilities, while noting the competitive media job market and tuition cost of a private graduate degree.",
        "themes": [
            {"label": "Practitioner-led training", "sentiment": "positive", "detail": "Courses are taught by working reporters and editors with current industry practice."},
            {"label": "Multimedia reporting skills", "sentiment": "positive", "detail": "Graduate curriculum spans investigative, digital, and broadcast reporting."},
            {"label": "Tough media job market", "sentiment": "caution", "detail": "Graduates must build strong portfolios and networks to land staff roles."},
        ],
        "sources": [
            {"label": "BU COM — Journalism graduate programs", "url": "https://www.bu.edu/com/academics/journalism/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sha-ms": {
        "summary": "BU's MS in Hospitality Administration (SHA) is a specialized graduate degree combining revenue management, operations, and leadership with required industry internships and global study options. Poets&Quants and hospitality rankings cite strong hotel-industry placement and faculty practitioner ties, while noting the niche focus compared with general MBA paths.",
        "themes": [
            {"label": "Industry-connected SHA", "sentiment": "positive", "detail": "Curriculum integrates property visits, internships, and hotel-management case work."},
            {"label": "Strong hospitality placement", "sentiment": "positive", "detail": "Graduates place into hotel, restaurant, and tourism leadership roles."},
            {"label": "Niche vs. general management", "sentiment": "mixed", "detail": "Degree is hospitality-specific; pivots may need supplemental business training."},
        ],
        "sources": [
            {"label": "BU School of Hospitality Administration", "url": "https://www.bu.edu/hospitality/"},
            {"label": "Poets&Quants — hospitality programs", "url": "https://poetsandquants.com/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-ssw-msw": {
        "summary": "BU's online MSW extends the School of Social Work's clinically focused training to working students, with the same CSWE-accredited curriculum as the on-campus program and extensive field-education requirements. Reviewers praise field-placement support and licensure preparation, while noting that online students must arrange local placements and that clinical social work is emotionally demanding.",
        "themes": [
            {"label": "CSWE-accredited online MSW", "sentiment": "positive", "detail": "Online students complete the same accredited curriculum and field hours."},
            {"label": "Field-education strength", "sentiment": "positive", "detail": "BU SSW is known for supervised clinical placements across diverse settings."},
            {"label": "Local placement logistics", "sentiment": "caution", "detail": "Online students must secure approved field sites near their residence."},
        ],
        "sources": [
            {"label": "BU School of Social Work — MSW Online", "url": "https://www.bu.edu/ssw/academics/msw/"},
            {"label": "U.S. News — social work rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mba-mph": {
        "summary": "BU's dual MBA/MPH combines Questrom business training with the School of Public Health's top-10 MPH, aimed at health-sector leaders managing programs, policy, and operations. Coverage highlights interdisciplinary health-management careers in hospitals, biotech, and NGOs, while warning of the workload and cost of completing two graduate degrees concurrently.",
        "themes": [
            {"label": "Health-management dual credential", "sentiment": "positive", "detail": "Combines business strategy with accredited public-health training."},
            {"label": "Top-10 SPH foundation", "sentiment": "positive", "detail": "SPH ranks among the nation's leading schools of public health."},
            {"label": "Heavy dual-degree workload", "sentiment": "caution", "detail": "Pursuing MBA and MPH requirements simultaneously is time-intensive."},
        ],
        "sources": [
            {"label": "BU School of Public Health — dual degrees", "url": "https://www.bumc.bu.edu/sph/education/degrees-and-programs/dual-degrees/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-busm-combined-md-mba": {
        "summary": "BU's MD/MBA dual degree trains physician-leaders through the Chobanian & Avedisian School of Medicine and Questrom, targeting students pursuing health-care administration, biotech entrepreneurship, or policy roles. Reviewers value the combination of clinical training with business fundamentals and Boston's health-sector ecosystem, while noting the extended timeline and cost of two demanding degrees.",
        "themes": [
            {"label": "Physician-leader pipeline", "sentiment": "positive", "detail": "Program targets clinicians moving into management, policy, or venture roles."},
            {"label": "Boston health ecosystem", "sentiment": "positive", "detail": "Medical Campus and Questrom connect students to hospitals, biotech, and payers."},
            {"label": "Long, expensive dual path", "sentiment": "caution", "detail": "Completing MD and MBA requirements adds years and tuition beyond medicine alone."},
        ],
        "sources": [
            {"label": "BU School of Medicine — MD/MBA", "url": "https://www.bumc.bu.edu/busm/education/md-programs/dual-degree-programs/md-mba/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-computer-engineering-ms": {
        "summary": "BU's MS in Computer Engineering (ECE) offers graduate depth in embedded systems, communications, and hardware-software co-design with ties to photonics and robotics research. Reviewers highlight research lab access and Boston tech hiring, while noting that funding is limited compared with PhD paths and applicants should clarify thesis vs. coursework tracks.",
        "themes": [
            {"label": "Graduate ECE depth", "sentiment": "positive", "detail": "MS students specialize in communications, embedded systems, or signal processing."},
            {"label": "Research lab access", "sentiment": "positive", "detail": "ECE labs connect to photonics, robotics, and sensing research."},
            {"label": "Limited MS funding", "sentiment": "caution", "detail": "Most financial support targets PhD students; MS students often self-fund."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering — graduate", "url": "https://www.bu.edu/ece/academics/graduate-programs/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-mathematics-statistics-ba": {
        "summary": "BU's mathematics & statistics undergraduate major (CAS) provides rigorous pure and applied training with pathways into actuarial science, data science, and graduate math. Reviewers praise proof-based coursework and faculty research exposure, while noting that students aiming for industry analytics often pair the major with CS or economics coursework.",
        "themes": [
            {"label": "Rigorous math foundation", "sentiment": "positive", "detail": "Major covers analysis, algebra, probability, and statistics with proof-based courses."},
            {"label": "Graduate-school and quant paths", "sentiment": "positive", "detail": "Graduates pursue PhDs, actuarial exams, and quantitative industry roles."},
            {"label": "Add CS/econ for industry analytics", "sentiment": "mixed", "detail": "Industry data roles often require supplemental computing coursework."},
        ],
        "sources": [
            {"label": "BU Department of Mathematics & Statistics", "url": "https://www.bu.edu/math/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-bs": {
        "summary": "Metropolitan College's part-time/online BS in Computer Science serves working adults and transfer students seeking a BU undergraduate credential with flexibility. Reviewers value the accessibility and career-upgrading potential, while noting differences from the residential CAS/CDS CS paths in research exposure and campus recruiting.",
        "themes": [
            {"label": "Flexible undergraduate CS", "sentiment": "positive", "detail": "Evening and online options support working students completing a BS."},
            {"label": "Career-upgrading credential", "sentiment": "positive", "detail": "BU bachelor's helps professionals pivot into software roles."},
            {"label": "Less residential recruiting", "sentiment": "mixed", "detail": "Part-time students have fewer on-campus career-fair touchpoints."},
        ],
        "sources": [
            {"label": "BU MET — Computer Science undergraduate", "url": "https://www.bu.edu/met/academics/undergraduate/computer-science/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-biomedical-engineering-meng": {
        "summary": "BU's one-year MEng in Biomedical Engineering is a practice-oriented, STEM-eligible graduate degree combining advanced BME coursework with a team-based design project and ties to the Medical Campus and affiliated hospitals. Reviewers highlight clinical proximity, device and imaging research labs, and Boston biotech hiring, while noting the accelerated pace and that most funding targets PhD students.",
        "themes": [
            {"label": "Medical-campus integration", "sentiment": "positive", "detail": "MEng students collaborate with clinicians and researchers across BU's Medical Campus."},
            {"label": "Design-project capstone", "sentiment": "positive", "detail": "Team-based biomedical design projects build portfolio-ready engineering experience."},
            {"label": "Accelerated one-year format", "sentiment": "caution", "detail": "The compressed schedule demands strong engineering preparation."},
        ],
        "sources": [
            {"label": "BU Biomedical Engineering — MEng", "url": "https://www.bu.edu/bme/academics/graduate/meng/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-biomedical-engineering-ms": {
        "summary": "The BU MS in Biomedical Engineering offers thesis and non-thesis tracks with research in neural, cardiac, and imaging systems at the intersection of engineering and medicine. Graduate guides praise interdisciplinary faculty, hospital partnerships, and placement into med-device and biotech roles, while warning that MS funding is limited and thesis students must secure advisor support early.",
        "themes": [
            {"label": "Interdisciplinary BME research", "sentiment": "positive", "detail": "Faculty span neural engineering, medical imaging, and tissue engineering."},
            {"label": "Boston biotech pipeline", "sentiment": "positive", "detail": "Graduates recruit into device, pharma, and health-tech firms in the region."},
            {"label": "Limited MS funding", "sentiment": "caution", "detail": "Most assistantships go to PhD students; MS applicants often self-fund."},
        ],
        "sources": [
            {"label": "BU Biomedical Engineering — graduate", "url": "https://www.bu.edu/bme/academics/graduate/"},
            {"label": "U.S. News — BU engineering rankings", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/boston-university-02073"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-mechanical-engineering-ms": {
        "summary": "BU's MS in Mechanical Engineering provides graduate depth in thermofluids, robotics, materials, and dynamics with access to research labs and co-op pathways. Reviewers cite solid fundamentals, Boston aerospace and robotics hiring, and project-based learning, while noting that applicants should clarify thesis vs. coursework tracks and funding expectations.",
        "themes": [
            {"label": "Broad ME graduate training", "sentiment": "positive", "detail": "Students specialize through electives in robotics, fluids, and design."},
            {"label": "Industry and research labs", "sentiment": "positive", "detail": "Labs connect to robotics, manufacturing, and energy research."},
            {"label": "Self-funded MS common", "sentiment": "caution", "detail": "Financial support is more available at the PhD level than for MS students."},
        ],
        "sources": [
            {"label": "BU Mechanical Engineering — graduate", "url": "https://www.bu.edu/me/academics/graduate/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-electrical-engineering-ms": {
        "summary": "BU's MS in Electrical & Computer Engineering spans communications, photonics, embedded systems, and signal processing with ties to the Photonics Center. Reviewers highlight photonics and RF strengths, Boston defense and tech recruiting, and research lab access, while noting competitive admissions and limited MS assistantships.",
        "themes": [
            {"label": "Photonics and communications", "sentiment": "positive", "detail": "ECE research strengths include optics, RF, and embedded systems."},
            {"label": "Boston tech hiring", "sentiment": "positive", "detail": "Graduates place into defense, telecom, and semiconductor firms."},
            {"label": "Limited MS funding", "sentiment": "caution", "detail": "Most tuition support targets doctoral students."},
        ],
        "sources": [
            {"label": "BU Electrical & Computer Engineering — graduate", "url": "https://www.bu.edu/ece/academics/graduate-programs/"},
            {"label": "BU Photonics Center", "url": "https://www.bu.edu/photonics/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-materials-science-engineering-ms": {
        "summary": "BU's MS in Materials Science & Engineering covers polymers, biomaterials, and nanomaterials with ties to the Photonics Center and Medical Campus. Department materials and graduate guides emphasize hands-on characterization labs and interdisciplinary research, while noting that MS students should identify a research advisor early for thesis tracks.",
        "themes": [
            {"label": "Materials and biomaterials research", "sentiment": "positive", "detail": "Faculty work spans polymers, nanomaterials, and biomedical interfaces."},
            {"label": "Shared characterization facilities", "sentiment": "positive", "detail": "Students access electron microscopy and spectroscopy labs."},
            {"label": "Advisor-dependent thesis path", "sentiment": "mixed", "detail": "Thesis students need faculty sponsorship before admission."},
        ],
        "sources": [
            {"label": "BU Materials Science & Engineering", "url": "https://www.bu.edu/mse/"},
            {"label": "U.S. News — BU engineering rankings", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/boston-university-02073"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-systems-engineering-ms": {
        "summary": "BU's MS in Systems Engineering (through the Division of Systems Engineering) trains engineers in model-based systems design, optimization, and lifecycle management for complex products. Reviewers value the interdisciplinary curriculum and defense/aerospace industry ties in the Boston corridor, while noting the program is smaller and less brand-visible than peer ECE or ME degrees.",
        "themes": [
            {"label": "Model-based systems design", "sentiment": "positive", "detail": "Coursework covers requirements, architecture, and verification of complex systems."},
            {"label": "Defense and aerospace ties", "sentiment": "positive", "detail": "Boston-area contractors recruit systems-trained engineers."},
            {"label": "Smaller program visibility", "sentiment": "mixed", "detail": "Systems engineering is less widely marketed than core ECE/ME paths."},
        ],
        "sources": [
            {"label": "BU Systems Engineering", "url": "https://www.bu.edu/se/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-biomedical-engineering-phd": {
        "summary": "BU's PhD in Biomedical Engineering is a research-intensive doctorate with strengths in neural engineering, cardiac systems, and medical imaging across the Charles River and Medical campuses. Reviewers praise NIH-funded labs, clinical collaborations, and placement into academia and industry R&D, while noting competitive admissions and the multi-year nature of doctoral training.",
        "themes": [
            {"label": "NIH-funded BME research", "sentiment": "positive", "detail": "Doctoral students join labs in neural, cardiac, and imaging systems."},
            {"label": "Clinical collaboration", "sentiment": "positive", "detail": "Medical Campus partnerships support translational research."},
            {"label": "Long, selective path", "sentiment": "caution", "detail": "PhD admission is competitive and typically fully funded for admitted students."},
        ],
        "sources": [
            {"label": "BU Biomedical Engineering — PhD", "url": "https://www.bu.edu/bme/academics/graduate/phd/"},
            {"label": "U.S. News — biomedical engineering rankings", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/biomedical-engineering-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-mechanical-engineering-phd": {
        "summary": "BU's PhD in Mechanical Engineering supports dissertation research in robotics, fluid mechanics, acoustics, and materials with funded assistantships for admitted students. Graduate community guides highlight interdisciplinary ties to the Photonics Center and aerospace partners, while noting that applicants must align with a faculty advisor's active research area.",
        "themes": [
            {"label": "Funded doctoral research", "sentiment": "positive", "detail": "Admitted PhD students typically receive tuition support and stipends."},
            {"label": "Robotics and fluids labs", "sentiment": "positive", "detail": "Dissertation areas span robotics, acoustics, and energy systems."},
            {"label": "Advisor match required", "sentiment": "caution", "detail": "Admission depends on faculty sponsorship in a specific research group."},
        ],
        "sources": [
            {"label": "BU Mechanical Engineering — PhD", "url": "https://www.bu.edu/me/academics/graduate/phd/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-electrical-engineering-phd": {
        "summary": "BU's PhD in Electrical & Computer Engineering is a research doctorate spanning photonics, communications, robotics, and embedded systems with strong ties to the Photonics Center. Reviewers cite funded assistantships, Boston industry collaborations, and placement into academia and R&D labs, while noting that applicants must demonstrate alignment with faculty research groups.",
        "themes": [
            {"label": "Photonics and ECE research", "sentiment": "positive", "detail": "Doctoral students join labs in optics, RF, robotics, and embedded systems."},
            {"label": "Funded PhD assistantships", "sentiment": "positive", "detail": "Admitted doctoral students typically receive tuition and stipend support."},
            {"label": "Faculty alignment critical", "sentiment": "caution", "detail": "Admission requires a faculty advisor willing to sponsor the applicant."},
        ],
        "sources": [
            {"label": "BU ECE — PhD program", "url": "https://www.bu.edu/ece/academics/graduate-programs/phd/"},
            {"label": "BU Photonics Center", "url": "https://www.bu.edu/photonics/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-computer-engineering-phd": {
        "summary": "BU's PhD in Computer Engineering (through ECE) focuses on hardware-software co-design, embedded systems, and communications with access to photonics and robotics labs. Graduate guides emphasize interdisciplinary research and funded assistantships for admitted students, while noting the program shares admissions and advising with the broader ECE doctoral portfolio.",
        "themes": [
            {"label": "Hardware-software research", "sentiment": "positive", "detail": "Dissertation areas include embedded systems, architecture, and communications."},
            {"label": "Shared ECE doctoral ecosystem", "sentiment": "positive", "detail": "Students access photonics, robotics, and sensing research centers."},
            {"label": "Advisor sponsorship required", "sentiment": "caution", "detail": "PhD admission depends on faculty research fit and funding."},
        ],
        "sources": [
            {"label": "BU ECE — PhD program", "url": "https://www.bu.edu/ece/academics/graduate-programs/phd/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-computer-science-ms": {
        "summary": "BU's MS in Computer Science (Graduate School of Arts & Sciences, through CAS) is a research-oriented master's with thesis and non-thesis options and strengths in AI, systems, and security. Reviewers compare it with the newer CDS MSDS path, noting GRS CS offers deeper theory and faculty research access while requiring stronger math preparation and offering fewer structured career services than professional analytics degrees.",
        "themes": [
            {"label": "Research-oriented CS master's", "sentiment": "positive", "detail": "Thesis track connects students to CAS/GRS faculty research labs."},
            {"label": "AI and systems depth", "sentiment": "positive", "detail": "Coursework spans theory, systems, and machine learning."},
            {"label": "Less career-structured than CDS/Questrom", "sentiment": "mixed", "detail": "Students must proactively pursue internships and recruiting."},
        ],
        "sources": [
            {"label": "BU Department of Computer Science — graduate", "url": "https://www.bu.edu/cs/graduate/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-computer-science-ms-in-artificial-intelligence": {
        "summary": "BU's MS in Computer Science with an artificial-intelligence focus (GRS/CAS) concentrates electives and thesis work in machine learning, NLP, and computer vision. Coverage highlights faculty in AI and robotics and Boston tech hiring, while noting overlap with the CDS MSDS program and that students must build their AI specialization through electives rather than a separate admissions track.",
        "themes": [
            {"label": "AI-focused CS electives", "sentiment": "positive", "detail": "Students concentrate in ML, vision, and NLP through CS graduate coursework."},
            {"label": "Faculty research access", "sentiment": "positive", "detail": "AI labs span CS, CDS, and ECE across campus."},
            {"label": "Overlap with CDS MSDS", "sentiment": "mixed", "detail": "Applicants should compare GRS CS vs. CDS MSDS for career vs. research goals."},
        ],
        "sources": [
            {"label": "BU Department of Computer Science — graduate", "url": "https://www.bu.edu/cs/graduate/"},
            {"label": "BU Faculty of Computing & Data Sciences", "url": "https://www.bu.edu/cds/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-computer-science-phd": {
        "summary": "BU's PhD in Computer Science (GRS/CAS) is a research doctorate with funded assistantships for admitted students and strengths in AI, systems, security, and theory. Reviewers praise the Hariri Institute ecosystem, Boston tech recruiting for graduates who industry-place, and competitive but collegial cohorts, while noting admission requires faculty alignment and strong mathematical preparation.",
        "themes": [
            {"label": "Funded CS doctoral research", "sentiment": "positive", "detail": "Admitted PhD students receive tuition support and stipends."},
            {"label": "AI and systems faculty", "sentiment": "positive", "detail": "Research spans machine learning, security, graphics, and robotics."},
            {"label": "Selective, advisor-matched admission", "sentiment": "caution", "detail": "Applicants need sponsorship from a faculty research group."},
        ],
        "sources": [
            {"label": "BU CS — PhD program", "url": "https://www.bu.edu/cs/graduate/phd/"},
            {"label": "Hariri Institute for Computing", "url": "https://www.bu.edu/hic/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-economics-ma": {
        "summary": "BU's MA in Economics (Graduate School of Arts & Sciences) provides rigorous micro, macro, and econometrics training aimed at PhD preparation and quantitative policy or finance roles. Reviewers highlight proof-based coursework, faculty research in macro and development, and placement into doctoral programs and Boston finance/policy employers, while noting the MA is academically demanding and not a professional business degree.",
        "themes": [
            {"label": "Rigorous econ MA training", "sentiment": "positive", "detail": "Core covers micro, macro, and econometrics at the graduate level."},
            {"label": "PhD prep and quant roles", "sentiment": "positive", "detail": "Graduates pursue doctoral study or analyst roles in finance and policy."},
            {"label": "Not a professional MBA substitute", "sentiment": "caution", "detail": "The MA is theory-heavy; industry recruiting requires proactive networking."},
        ],
        "sources": [
            {"label": "BU Department of Economics — MA", "url": "https://www.bu.edu/econ/graduate/masters-program/"},
            {"label": "U.S. News — BU rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cds-phd-in-computing-data-sciences": {
        "summary": "BU's PhD in Computing & Data Sciences is an interdisciplinary doctorate housed in the Faculty of Computing & Data Sciences, spanning statistics, ML, and responsible computing. Official CDS materials and graduate guides emphasize cross-college advising, the new Center for Computing & Data Sciences building, and funded assistantships for admitted students, while noting the program is young compared with peer CS PhDs.",
        "themes": [
            {"label": "Interdisciplinary CDS doctorate", "sentiment": "positive", "detail": "Students combine computing, statistics, and domain applications."},
            {"label": "New academic unit", "sentiment": "positive", "detail": "CDS is a purpose-built faculty spanning BU's colleges."},
            {"label": "Younger than peer CS PhDs", "sentiment": "mixed", "detail": "Track record is still building versus decades-old CS departments."},
        ],
        "sources": [
            {"label": "BU CDS — PhD program", "url": "https://www.bu.edu/cds-faculty/programs-admissions/phd-computing-data-sciences/"},
            {"label": "BU Faculty of Computing & Data Sciences", "url": "https://www.bu.edu/cds/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-jdmba": {
        "summary": "BU's JD/MBA dual degree combines the School of Law's nationally ranked JD with Questrom's MBA, typically completed in four years for students pursuing corporate law, finance, or consulting careers. Reviewers value the time savings versus sequential degrees, Boston's legal and business markets, and interdisciplinary health and IP offerings, while noting the workload and cost of two professional degrees.",
        "themes": [
            {"label": "Combined law and business training", "sentiment": "positive", "detail": "Students earn both JD and MBA credentials in an integrated curriculum."},
            {"label": "Boston legal and finance market", "sentiment": "positive", "detail": "Dual-degree graduates recruit into firms, banks, and corporate counsel roles."},
            {"label": "Heavy dual-degree workload", "sentiment": "caution", "detail": "Completing law and business requirements simultaneously is demanding."},
        ],
        "sources": [
            {"label": "BU Law — JD/MBA", "url": "https://www.bu.edu/law/academics/degree-programs/dual-degree/jd-mba/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-jdmba-health": {
        "summary": "BU's JD/MBA with a health-sector management focus targets attorneys and managers in hospitals, biotech, and health-policy organizations by combining law, business, and health-system coursework. Coverage highlights Boston's hospital ecosystem and Questrom/SPH cross-registration, while warning of the extended timeline and tuition of two professional degrees plus health-sector electives.",
        "themes": [
            {"label": "Health-sector leadership pipeline", "sentiment": "positive", "detail": "Combines legal training with health-management business skills."},
            {"label": "Boston hospital ecosystem", "sentiment": "positive", "detail": "Medical Campus and Questrom connect students to providers and biotech."},
            {"label": "Extended, costly path", "sentiment": "caution", "detail": "Dual professional degrees plus health electives add time and tuition."},
        ],
        "sources": [
            {"label": "BU Law — JD/MBA health sector", "url": "https://www.bu.edu/law/academics/degree-programs/dual-degree/jd-mba/"},
            {"label": "BU School of Public Health", "url": "https://www.bumc.bu.edu/sph/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-jdmph": {
        "summary": "BU's JD/MPH dual degree pairs the School of Law with the top-10 School of Public Health for careers in health law, policy, and advocacy. Reviewers cite interdisciplinary faculty, Boston's health-policy community, and strong SPH reputation, while noting the workload of completing both a professional law degree and an accredited MPH.",
        "themes": [
            {"label": "Health law and policy focus", "sentiment": "positive", "detail": "Combines legal training with accredited public-health coursework."},
            {"label": "Top-10 SPH partner", "sentiment": "positive", "detail": "SPH ranks among the nation's leading schools of public health."},
            {"label": "Dual-degree workload", "sentiment": "caution", "detail": "Law and MPH requirements must be completed in parallel or sequence."},
        ],
        "sources": [
            {"label": "BU Law — JD/MPH", "url": "https://www.bu.edu/law/academics/degree-programs/dual-degree/jd-mph/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-phd-in-business-economics": {
        "summary": "Questrom's PhD in Business Economics is a rigorous doctoral program training scholars in microeconomics, econometrics, and applied fields for academia and research roles. Reviewers highlight funded assistantships, faculty ties to the economics department, and placement into research universities, while noting the multi-year commitment and that it is distinct from a professional MBA.",
        "themes": [
            {"label": "Funded business-economics doctorate", "sentiment": "positive", "detail": "Admitted students receive tuition support and research assistantships."},
            {"label": "Econometrics and applied fields", "sentiment": "positive", "detail": "Training spans theory, empirical methods, and field courses."},
            {"label": "Academic career focus", "sentiment": "caution", "detail": "The PhD targets research and teaching, not industry management roles."},
        ],
        "sources": [
            {"label": "Questrom — PhD in Business Economics", "url": "https://www.bu.edu/questrom/graduate-programs/phd-program/"},
            {"label": "U.S. News — Questrom MBA rankings", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/boston-university-01097"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-product-design-manufacture-msmba": {
        "summary": "BU's MS/MBA in Product Design & Manufacture combines engineering product-development coursework with Questrom business fundamentals for students pursuing hardware and manufacturing leadership. Reviewers value the interdisciplinary capstone and Boston manufacturing and robotics ties, while noting the cost and pace of completing both degrees.",
        "themes": [
            {"label": "Engineering + business blend", "sentiment": "positive", "detail": "Students combine product design engineering with MBA core courses."},
            {"label": "Manufacturing and robotics ties", "sentiment": "positive", "detail": "Boston-area firms support internships in product development."},
            {"label": "Dual-degree cost and pace", "sentiment": "caution", "detail": "Completing MS and MBA requirements adds time and tuition."},
        ],
        "sources": [
            {"label": "BU Mechanical Engineering — Product Design", "url": "https://www.bu.edu/me/academics/graduate/product-design-manufacture/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-busm-combined-mdjd": {
        "summary": "BU's MD/JD dual degree trains physician-attorneys for careers in health law, medical ethics, and health-policy leadership by combining the Chobanian & Avedisian MD with the nationally ranked School of Law JD. Reviewers value the rare credential, Boston's legal and medical ecosystem, and policy pathways, while warning of the extended timeline and cost of two demanding professional degrees.",
        "themes": [
            {"label": "Physician-attorney credential", "sentiment": "positive", "detail": "Graduates pursue health law, policy, and medical-legal consulting."},
            {"label": "Boston medical and legal hub", "sentiment": "positive", "detail": "Medical Campus and Law School connect students to hospitals and firms."},
            {"label": "Very long, expensive path", "sentiment": "caution", "detail": "Completing MD and JD requirements extends training by multiple years."},
        ],
        "sources": [
            {"label": "BU School of Medicine — MD/JD", "url": "https://www.bumc.bu.edu/busm/education/md-programs/dual-degree-programs/md-jd/"},
            {"label": "BU School of Law", "url": "https://www.bu.edu/law/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-epidemiology-and-biostatistics": {
        "summary": "BU SPH's epidemiology and biostatistics MPH concentration builds quantitative skills for disease surveillance, clinical research, and public-health analytics in one of the nation's top-10 schools of public health. Reviewers praise faculty leadership in epidemiology, rigorous biostatistics training, and Boston hospital data access, while noting the quant-heavy coursework requires strong math preparation.",
        "themes": [
            {"label": "Quantitative public-health training", "sentiment": "positive", "detail": "Coursework spans epidemiologic methods, biostatistics, and data analysis."},
            {"label": "Top-10 SPH reputation", "sentiment": "positive", "detail": "BU SPH ranks among the leading U.S. schools of public health."},
            {"label": "Math-intensive", "sentiment": "caution", "detail": "Biostatistics tracks demand strong quantitative backgrounds."},
        ],
        "sources": [
            {"label": "BU SPH — Epidemiology", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/epidemiology/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-health-policy-and-law": {
        "summary": "BU SPH's health policy and law MPH concentration combines public-health policy analysis with legal frameworks for students pursuing roles in government, advocacy, and health-system regulation. Reviewers highlight interdisciplinary faculty, Boston's policy community, and ties to BU Law, while noting that legal careers still require a JD for practice.",
        "themes": [
            {"label": "Policy and legal frameworks", "sentiment": "positive", "detail": "Curriculum covers health policy analysis, regulation, and advocacy."},
            {"label": "Boston policy ecosystem", "sentiment": "positive", "detail": "Internships span government, NGOs, and health systems."},
            {"label": "JD needed for legal practice", "sentiment": "caution", "detail": "The MPH alone does not qualify graduates to practice law."},
        ],
        "sources": [
            {"label": "BU SPH — Health Policy & Law", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/health-policy-and-law/"},
            {"label": "BU School of Public Health", "url": "https://www.bumc.bu.edu/sph/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-environmental-health": {
        "summary": "BU SPH's environmental health MPH concentration trains practitioners in exposure science, occupational health, and climate-related health risks. Official SPH materials and rankings coverage highlight faculty research in environmental epidemiology and Boston's public-health agencies as internship sites, while noting lab and fieldwork components can be demanding.",
        "themes": [
            {"label": "Environmental and occupational health", "sentiment": "positive", "detail": "Coursework covers exposure assessment, toxicology, and risk analysis."},
            {"label": "Research-active faculty", "sentiment": "positive", "detail": "SPH labs study air quality, climate, and occupational hazards."},
            {"label": "Field and lab workload", "sentiment": "caution", "detail": "Some tracks require substantial fieldwork or lab components."},
        ],
        "sources": [
            {"label": "BU SPH — Environmental Health", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/environmental-health/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-global-health-2": {
        "summary": "BU SPH's global health MPH concentration prepares practitioners for international NGOs, multilateral agencies, and cross-border health programs with strengths in infectious disease and health systems. Reviewers cite BU's global-health research centers, field practicum options, and top-10 SPH ranking, while noting that overseas placements require planning and funding.",
        "themes": [
            {"label": "Global-health research centers", "sentiment": "positive", "detail": "Faculty work on infectious disease, health systems, and equity abroad."},
            {"label": "Field practicum options", "sentiment": "positive", "detail": "Students complete practica with international and domestic partners."},
            {"label": "Overseas placement logistics", "sentiment": "caution", "detail": "International fieldwork requires advance planning and often self-funded travel."},
        ],
        "sources": [
            {"label": "BU SPH — Global Health", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/global-health/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-healthcare-management": {
        "summary": "BU SPH's healthcare management MPH concentration targets managers and analysts in hospitals, payers, and health-tech firms, blending public-health fundamentals with management coursework and Questrom cross-registration options. Reviewers highlight Boston's hospital market and the MBA/MPH dual-degree pathway, while noting management roles often benefit from supplemental business training.",
        "themes": [
            {"label": "Health-system management focus", "sentiment": "positive", "detail": "Curriculum covers health economics, operations, and policy for managers."},
            {"label": "Boston hospital market", "sentiment": "positive", "detail": "Internships span major hospital systems and payers in the region."},
            {"label": "Supplemental business training helpful", "sentiment": "mixed", "detail": "Senior management roles may require MBA or equivalent experience."},
        ],
        "sources": [
            {"label": "BU SPH — Health Management & Policy", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/health-management-policy/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-mscis": {
        "summary": "MET's MS in Computer Information Systems is a long-running professional graduate degree blending software development, data analytics, and IT management for working technologists, available online and on campus. Reviewers value the flexibility, BU credential, and Boston employer recognition, while noting it is broader and less research-focused than the residential GRS CS or CDS MSDS paths.",
        "themes": [
            {"label": "Professional IT and CS blend", "sentiment": "positive", "detail": "Concentrations span software engineering, data analytics, and IT management."},
            {"label": "Working-adult flexibility", "sentiment": "positive", "detail": "Evening and online formats suit career advancement without leaving work."},
            {"label": "Less research depth than GRS/CDS", "sentiment": "mixed", "detail": "MSCIS is practitioner-oriented rather than thesis-research focused."},
        ],
        "sources": [
            {"label": "BU MET — Computer Information Systems", "url": "https://www.bu.edu/met/academics/graduate/computer-information-systems/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-economics": {
        "summary": "MET's undergraduate economics degree serves working adults and transfer students seeking a BU bachelor's with evening and online flexibility. Reviewers appreciate the accessibility and career-upgrading potential for analysts and policy roles, while noting fewer research and on-campus recruiting opportunities than the residential CAS economics major.",
        "themes": [
            {"label": "Flexible economics bachelor's", "sentiment": "positive", "detail": "Part-time and online options support working students."},
            {"label": "BU credential for analysts", "sentiment": "positive", "detail": "Degree supports roles in finance, policy, and business analysis."},
            {"label": "Less residential recruiting", "sentiment": "mixed", "detail": "Part-time students have fewer on-campus career-fair touchpoints."},
        ],
        "sources": [
            {"label": "BU MET — Economics", "url": "https://www.bu.edu/met/academics/undergraduate/economics/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-graduate-program-in-banking-financial-law": {
        "summary": "BU Law's LLM in Banking & Financial Law is a nationally recognized specialty program for domestic and international lawyers focusing on securities, banking regulation, and financial transactions. Reviewers cite BU's top-ranked financial-law faculty, Boston's asset-management hub, and strong alumni network, while noting the program is designed for lawyers rather than career changers without a JD.",
        "themes": [
            {"label": "Top financial-law specialty", "sentiment": "positive", "detail": "BU Law is widely cited for banking and securities law strength."},
            {"label": "Boston finance market", "sentiment": "positive", "detail": "Graduates place into banks, asset managers, and regulatory roles."},
            {"label": "Requires prior legal training", "sentiment": "caution", "detail": "The LLM assumes a JD or equivalent foreign law degree."},
        ],
        "sources": [
            {"label": "BU Law — Banking & Financial Law LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/banking-financial-law/"},
            {"label": "U.S. News — BU School of Law", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-intellectual-property-law": {
        "summary": "BU Law's LLM in Intellectual Property & Information Law is a leading specialty degree covering patents, copyright, tech licensing, and information policy for attorneys and tech-sector professionals with legal training. Reviewers highlight faculty expertise, Boston's biotech and tech sectors, and national IP rankings, while noting admission expects prior legal credentials.",
        "themes": [
            {"label": "Leading IP specialty program", "sentiment": "positive", "detail": "BU Law's IP program is consistently ranked among the nation's best."},
            {"label": "Biotech and tech sector ties", "sentiment": "positive", "detail": "Boston employers recruit IP-trained attorneys for life sciences and tech."},
            {"label": "Prior legal degree expected", "sentiment": "caution", "detail": "The LLM is for lawyers, not a substitute for a JD."},
        ],
        "sources": [
            {"label": "BU Law — IP & Information Law LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/intellectual-property-law/"},
            {"label": "U.S. News — IP law rankings", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/intellectual-property-law-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-materials-science-engineering-meng": {
        "summary": "BU's Master of Engineering in Materials Science & Engineering is a practice-oriented graduate degree focused on advanced materials, nanotechnology, and manufacturing for industry roles. Reviewers cite strong ties to BU's Photonics Center and biomedical materials research, Boston's advanced-manufacturing sector, and the MEng's shorter timeline versus a research PhD, while noting it is less research-intensive than a thesis-based MS.",
        "themes": [
            {"label": "Industry-focused MEng", "sentiment": "positive", "detail": "Coursework emphasizes applied materials science and engineering design."},
            {"label": "Photonics and biomaterials research", "sentiment": "positive", "detail": "Faculty labs span photonics, polymers, and biomedical materials."},
            {"label": "Less thesis research than MS/PhD", "sentiment": "mixed", "detail": "The MEng targets professional practice rather than academic research."},
        ],
        "sources": [
            {"label": "BU Materials Science & Engineering — MEng", "url": "https://www.bu.edu/eng/academics/departments-and-divisions/materials-science-engineering/graduate/meng/"},
            {"label": "U.S. News — engineering rankings", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/boston-university-01096"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-systems-engineering-meng": {
        "summary": "BU's MEng in Systems Engineering trains engineers to model, optimize, and manage complex systems across aerospace, defense, healthcare, and technology. Reviewers highlight interdisciplinary coursework, connections to BU's Division of Systems Engineering, and Boston defense and healthcare employers, while noting the program expects prior engineering fundamentals.",
        "themes": [
            {"label": "Complex systems focus", "sentiment": "positive", "detail": "Curriculum covers systems modeling, optimization, and project management."},
            {"label": "Defense and healthcare applications", "sentiment": "positive", "detail": "Boston-area employers recruit systems engineers for regulated industries."},
            {"label": "Engineering background expected", "sentiment": "caution", "detail": "Applicants typically need prior engineering or quantitative training."},
        ],
        "sources": [
            {"label": "BU Systems Engineering — MEng", "url": "https://www.bu.edu/eng/academics/departments-and-divisions/systems-engineering/graduate/meng/"},
            {"label": "U.S. News — engineering rankings", "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/boston-university-01096"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-computer-science-ba-ms": {
        "summary": "BU's combined BA/MS in Computer Science lets undergraduates in CAS earn a master's with an accelerated fifth year, building on the department's strengths in AI, systems, and security. Reviewers praise the streamlined path to graduate credentials, faculty research access, and Boston tech recruiting, while noting admission to the combined track is competitive and requires strong CS performance.",
        "themes": [
            {"label": "Accelerated BA-to-MS path", "sentiment": "positive", "detail": "Qualified undergraduates can complete the MS in a fifth year."},
            {"label": "Research-active CS department", "sentiment": "positive", "detail": "Students access AI, security, and systems labs before graduate coursework."},
            {"label": "Selective combined admission", "sentiment": "caution", "detail": "Students must meet GPA and prerequisite thresholds for the MS year."},
        ],
        "sources": [
            {"label": "BU CS — BA/MS program", "url": "https://www.bu.edu/cs/academics/undergraduate-programs/combined-ba-ms/"},
            {"label": "BU Department of Computer Science", "url": "https://www.bu.edu/cs/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-ms-in-health-informatics": {
        "summary": "MET's online MS in Computer Science with a health informatics concentration trains working professionals to build clinical data systems, EHR integrations, and health-analytics tools. Reviewers value the part-time online format, BU's Medical Campus proximity, and Boston hospital IT demand, while noting the program is practitioner-focused rather than a clinical degree.",
        "themes": [
            {"label": "Online, part-time format", "sentiment": "positive", "detail": "Designed for professionals balancing work and graduate study."},
            {"label": "Health IT and clinical data", "sentiment": "positive", "detail": "Coursework covers health informatics standards, databases, and analytics."},
            {"label": "Not a clinical credential", "sentiment": "caution", "detail": "The degree prepares technologists, not licensed clinicians."},
        ],
        "sources": [
            {"label": "MET — MS CS Health Informatics", "url": "https://www.bu.edu/met/programs/computer-science/ms-in-health-informatics/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-ms-in-software-development": {
        "summary": "MET's online MS in Computer Science with a software development concentration targets mid-career engineers seeking advanced software engineering, cloud, and agile skills without leaving the workforce. Reviewers highlight flexible evening/online delivery, practical project work, and Boston tech employer recognition of BU credentials, while noting it is less research-oriented than the on-campus GRS CS MS.",
        "themes": [
            {"label": "Practical software engineering", "sentiment": "positive", "detail": "Curriculum emphasizes software design, development, and deployment."},
            {"label": "Working-professional friendly", "sentiment": "positive", "detail": "Part-time and online options suit employed engineers."},
            {"label": "Less research focus than campus MS", "sentiment": "mixed", "detail": "The MET track prioritizes applied skills over thesis research."},
        ],
        "sources": [
            {"label": "MET — MS CS Software Development", "url": "https://www.bu.edu/met/programs/computer-science/ms-in-software-development/"},
            {"label": "U.S. News — BU online rankings", "url": "https://www.usnews.com/best-colleges/boston-university-2130"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-telecommunication": {
        "summary": "MET's MS in Computer Science with a telecommunication concentration covers networking, wireless systems, and cloud infrastructure for professionals in telecom and IT. Reviewers cite BU's long-standing MET reputation for part-time graduate education and Boston's telecom sector, while noting the concentration name reflects legacy telecom framing though coursework spans modern networking.",
        "themes": [
            {"label": "Networking and telecom focus", "sentiment": "positive", "detail": "Coursework spans data networks, wireless, and cloud systems."},
            {"label": "Part-time graduate tradition", "sentiment": "positive", "detail": "MET has decades of experience serving working professionals."},
            {"label": "Legacy concentration label", "sentiment": "mixed", "detail": "The telecommunication title predates cloud-era naming but covers modern topics."},
        ],
        "sources": [
            {"label": "MET — MS CS Telecommunication", "url": "https://www.bu.edu/met/programs/computer-science/telecommunication/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-economics-ma-mba": {
        "summary": "BU's MA/MBA dual degree pairs the Graduate School of Arts & Sciences economics MA with Questrom's MBA for students pursuing policy, consulting, and finance leadership. Reviewers value the quantitative economics foundation plus business training, Boston employer access, and Questrom's thematic strengths, while noting the extended timeline and cost of completing both degrees.",
        "themes": [
            {"label": "Economics plus MBA", "sentiment": "positive", "detail": "Combines rigorous economics coursework with Questrom business core."},
            {"label": "Boston finance and consulting market", "sentiment": "positive", "detail": "Dual-degree graduates recruit into analytics, consulting, and finance."},
            {"label": "Dual-degree time and cost", "sentiment": "caution", "detail": "Completing MA and MBA requirements extends study and tuition."},
        ],
        "sources": [
            {"label": "GRS — Economics MA/MBA", "url": "https://www.bu.edu/econ/graduate/ma-mba/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-bachelor-of-science-in-business-administration-bsba-to-master-of-science-in-business-analytics-msb": {
        "summary": "Questrom's combined BSBA-to-MSBA lets undergraduates earn a business analytics master's in an accelerated path, building on Questrom's growing analytics curriculum and Boston's data-driven employer market. Reviewers praise early exposure to analytics tools, the MSBA's industry relevance, and recruiting into consulting and tech, while noting the combined track requires strong quantitative performance.",
        "themes": [
            {"label": "Accelerated analytics path", "sentiment": "positive", "detail": "Undergraduates can progress directly into the MS in Business Analytics."},
            {"label": "Industry-relevant analytics training", "sentiment": "positive", "detail": "Coursework spans data mining, visualization, and business decision modeling."},
            {"label": "Quantitative admission bar", "sentiment": "caution", "detail": "Students need strong math and statistics preparation for the MSBA year."},
        ],
        "sources": [
            {"label": "Questrom — BSBA to MSBA", "url": "https://www.bu.edu/questrom/graduate-programs/ms-in-business-analytics/"},
            {"label": "U.S. News — Questrom MBA rankings", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/boston-university-01097"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-msdt": {
        "summary": "Questrom's MBA/MS in Digital Technology (MSDT) dual degree combines management fundamentals with deep digital-product and technology coursework for leaders in tech-driven industries. Reviewers highlight Questrom's digital-business theme, Boston tech and health-tech recruiting, and the rare MBA-plus-technical credential, while noting the workload of completing both degrees.",
        "themes": [
            {"label": "MBA plus digital technology MS", "sentiment": "positive", "detail": "Students gain business leadership and digital product/tech skills."},
            {"label": "Digital business theme", "sentiment": "positive", "detail": "Questrom emphasizes technology transformation across concentrations."},
            {"label": "Dual-degree workload", "sentiment": "caution", "detail": "MBA and MSDT requirements must be completed within the program timeline."},
        ],
        "sources": [
            {"label": "Questrom — MBA/MSDT", "url": "https://www.bu.edu/questrom/graduate-programs/ms-in-digital-technology/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-questrom-mathematical-finance-phd": {
        "summary": "Questrom's PhD in Mathematical Finance is a doctoral program training scholars in stochastic modeling, asset pricing, and financial econometrics for academia and quantitative finance. Reviewers cite funded assistantships, faculty ties to the economics and math departments, and placement into research and quant roles, while noting the multi-year commitment and highly selective admission.",
        "themes": [
            {"label": "Quantitative finance doctorate", "sentiment": "positive", "detail": "Training spans stochastic calculus, econometrics, and financial theory."},
            {"label": "Funded doctoral support", "sentiment": "positive", "detail": "Admitted students typically receive tuition support and research assistantships."},
            {"label": "Highly selective, long path", "sentiment": "caution", "detail": "The PhD requires years of coursework and dissertation research."},
        ],
        "sources": [
            {"label": "Questrom — PhD Mathematical Finance", "url": "https://www.bu.edu/questrom/graduate-programs/phd-program/mathematical-finance/"},
            {"label": "U.S. News — Questrom MBA rankings", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/boston-university-01097"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-medicine-and-public-health": {
        "summary": "BU's MD/MPH dual degree pairs the Chobanian & Avedisian School of Medicine with the top-10 School of Public Health for physician-leaders in population health, global health, and health policy. Reviewers value the rare combined credential, Boston's medical and public-health ecosystem, and SPH's accredited concentrations, while warning of the extended timeline and cost of two demanding professional degrees.",
        "themes": [
            {"label": "Physician plus public-health leader", "sentiment": "positive", "detail": "Graduates pursue academic medicine, global health, and health-policy roles."},
            {"label": "Top-10 SPH partner", "sentiment": "positive", "detail": "SPH ranks among the nation's leading schools of public health."},
            {"label": "Extended dual-degree path", "sentiment": "caution", "detail": "MD and MPH requirements add years and tuition beyond the MD alone."},
        ],
        "sources": [
            {"label": "BU Medicine — MD/MPH", "url": "https://www.bumc.bu.edu/busm/education/md-programs/dual-degree-programs/md-mph/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-chronic-and-non-communicable-diseases": {
        "summary": "BU SPH's chronic and non-communicable diseases MPH concentration prepares practitioners to address cardiovascular disease, diabetes, cancer, and other long-term conditions through epidemiology and prevention. Reviewers cite SPH's top-10 ranking, faculty research in chronic-disease epidemiology, and Boston hospital partnerships, while noting quantitative methods coursework can be demanding.",
        "themes": [
            {"label": "Chronic disease prevention focus", "sentiment": "positive", "detail": "Curriculum covers epidemiology, prevention, and health-system responses to NCDs."},
            {"label": "Top-10 SPH reputation", "sentiment": "positive", "detail": "BU SPH ranks among the leading U.S. schools of public health."},
            {"label": "Quantitative coursework", "sentiment": "caution", "detail": "Epidemiologic methods require comfort with statistics."},
        ],
        "sources": [
            {"label": "BU SPH — Chronic & NCD MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/chronic-and-non-communicable-diseases/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-community-assessment": {
        "summary": "BU SPH's community assessment MPH concentration trains practitioners to evaluate community health needs, design interventions, and partner with local organizations. Reviewers highlight applied practicum work, Boston community-health agencies as field sites, and SPH's community-health sciences department, while noting field placements require time beyond classroom study.",
        "themes": [
            {"label": "Community health assessment skills", "sentiment": "positive", "detail": "Coursework covers needs assessment, program planning, and evaluation."},
            {"label": "Boston community partners", "sentiment": "positive", "detail": "Practicum sites include local health departments and nonprofits."},
            {"label": "Fieldwork time commitment", "sentiment": "caution", "detail": "Community-based practica add hours beyond standard coursework."},
        ],
        "sources": [
            {"label": "BU SPH — Community Assessment MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/community-assessment/"},
            {"label": "BU School of Public Health", "url": "https://www.bumc.bu.edu/sph/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-monitoring-and-evaluation": {
        "summary": "BU SPH's monitoring and evaluation MPH concentration builds skills in program evaluation, impact measurement, and data-driven decision-making for NGOs, government, and global-health organizations. Reviewers praise the quantitative evaluation toolkit, global-health research centers, and SPH's top-10 ranking, while noting strong statistics preparation is helpful.",
        "themes": [
            {"label": "Program evaluation expertise", "sentiment": "positive", "detail": "Training spans M&E frameworks, indicators, and impact assessment."},
            {"label": "Global-health and NGO relevance", "sentiment": "positive", "detail": "Graduates work in development agencies and health nonprofits."},
            {"label": "Statistics helpful", "sentiment": "caution", "detail": "Evaluation methods coursework benefits from prior quantitative training."},
        ],
        "sources": [
            {"label": "BU SPH — Monitoring & Evaluation MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/monitoring-and-evaluation/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-in-health-equity": {
        "summary": "BU SPH's health equity MPH concentration addresses structural determinants of health, disparities, and justice-oriented public-health practice. Reviewers cite interdisciplinary faculty, Boston's diverse communities as learning contexts, and SPH's social-and-behavioral-sciences strength, while noting the concentration's advocacy orientation may differ from purely quantitative tracks.",
        "themes": [
            {"label": "Health disparities and justice", "sentiment": "positive", "detail": "Curriculum examines structural inequities and community-centered interventions."},
            {"label": "Boston diversity context", "sentiment": "positive", "detail": "Urban Boston provides diverse communities for practicum and research."},
            {"label": "Less quant-heavy than epi tracks", "sentiment": "mixed", "detail": "The concentration emphasizes social determinants over biostatistics depth."},
        ],
        "sources": [
            {"label": "BU SPH — Health Equity MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/health-equity/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-human-rights-and-social-justice": {
        "summary": "BU SPH's human rights and social justice MPH concentration connects public-health practice with human-rights frameworks for work in advocacy, global health, and policy. Reviewers highlight unique interdisciplinary framing, ties to BU's human-rights programs, and practicum opportunities with NGOs, while noting career paths are often mission-driven with variable compensation.",
        "themes": [
            {"label": "Human-rights and public-health link", "sentiment": "positive", "detail": "Coursework integrates rights-based approaches to health policy and practice."},
            {"label": "Advocacy and NGO pathways", "sentiment": "positive", "detail": "Graduates pursue roles in advocacy, global health, and nonprofits."},
            {"label": "Mission-driven careers", "sentiment": "mixed", "detail": "Advocacy and NGO roles may offer lower pay than industry public-health jobs."},
        ],
        "sources": [
            {"label": "BU SPH — Human Rights & Social Justice MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/human-rights-and-social-justice/"},
            {"label": "BU School of Public Health", "url": "https://www.bumc.bu.edu/sph/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-infectious-disease": {
        "summary": "BU SPH's infectious disease MPH concentration leverages BU's NEIDL-adjacent research ecosystem and epidemiology faculty for training in outbreak response, surveillance, and global infectious-disease control. Reviewers cite NEIDL proximity, top-10 SPH ranking, and Boston hospital epidemiology partnerships, while noting biosafety and fieldwork components in some tracks.",
        "themes": [
            {"label": "Infectious-disease research ecosystem", "sentiment": "positive", "detail": "BU's Medical Campus and NEIDL support infectious-disease research training."},
            {"label": "Outbreak and surveillance skills", "sentiment": "positive", "detail": "Coursework covers epidemiologic methods for infectious-disease control."},
            {"label": "Specialized field components", "sentiment": "caution", "detail": "Some tracks involve lab or fieldwork with additional safety requirements."},
        ],
        "sources": [
            {"label": "BU SPH — Infectious Disease MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/infectious-disease/"},
            {"label": "National Emerging Infectious Diseases Laboratories", "url": "https://www.bu.edu/neidl/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-maternal-and-child-health": {
        "summary": "BU SPH's maternal and child health MPH concentration trains practitioners in perinatal health, child development, and family-centered public-health programs. Reviewers praise the department's long-standing MCH focus, Boston children's hospitals as practicum sites, and SPH's top-10 ranking, while noting competitive practicum placements in pediatric settings.",
        "themes": [
            {"label": "MCH specialty training", "sentiment": "positive", "detail": "Curriculum covers maternal, infant, and child health policy and programs."},
            {"label": "Boston pediatric hospital access", "sentiment": "positive", "detail": "Practicum sites include major Boston children's hospitals."},
            {"label": "Competitive pediatric placements", "sentiment": "caution", "detail": "Desirable hospital practica require early planning."},
        ],
        "sources": [
            {"label": "BU SPH — Maternal & Child Health MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/maternal-and-child-health/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-mental-health-and-substance-use": {
        "summary": "BU SPH's mental health and substance use MPH concentration prepares practitioners for roles in behavioral-health policy, prevention, and community mental-health programs. Reviewers highlight interdisciplinary faculty spanning epidemiology and social sciences, Boston behavioral-health agencies, and growing employer demand, while noting the field's emotionally demanding practicum settings.",
        "themes": [
            {"label": "Behavioral-health public-health focus", "sentiment": "positive", "detail": "Training covers mental-health epidemiology, prevention, and policy."},
            {"label": "Growing field demand", "sentiment": "positive", "detail": "Employers seek public-health professionals with behavioral-health expertise."},
            {"label": "Emotionally demanding practica", "sentiment": "caution", "detail": "Community mental-health fieldwork can be intensive."},
        ],
        "sources": [
            {"label": "BU SPH — Mental Health & Substance Use MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/mental-health-and-substance-use/"},
            {"label": "BU School of Public Health", "url": "https://www.bumc.bu.edu/sph/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-pharmaceutical-development-delivery-and-access": {
        "summary": "BU SPH's pharmaceutical development, delivery, and access MPH concentration connects public-health practice with drug development, regulatory science, and global access to medicines — aligned with Boston's biopharma cluster. Reviewers cite proximity to biotech employers, SPH's health-policy faculty, and unique industry-facing curriculum, while noting some roles may require additional regulatory or scientific credentials.",
        "themes": [
            {"label": "Biopharma and access focus", "sentiment": "positive", "detail": "Curriculum spans drug development, delivery systems, and global access policy."},
            {"label": "Boston biotech ecosystem", "sentiment": "positive", "detail": "Graduates recruit into biopharma, regulatory affairs, and global health."},
            {"label": "May need additional credentials", "sentiment": "caution", "detail": "Some industry roles prefer science or regulatory certifications beyond the MPH."},
        ],
        "sources": [
            {"label": "BU SPH — Pharmaceutical Development MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/pharmaceutical-development-delivery-and-access/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-american-law": {
        "summary": "BU Law's LLM in American Law introduces foreign-trained lawyers to U.S. legal doctrine, procedure, and professional practice over one year. Reviewers cite BU Law's national reputation, Boston's legal market, and structured LLM curriculum, while noting the program does not qualify graduates to sit for every U.S. bar exam without additional requirements.",
        "themes": [
            {"label": "U.S. legal system introduction", "sentiment": "positive", "detail": "Coursework covers American legal institutions, doctrine, and practice skills."},
            {"label": "National law school reputation", "sentiment": "positive", "detail": "BU Law ranks among the top U.S. law schools."},
            {"label": "Bar eligibility varies by state", "sentiment": "caution", "detail": "Foreign LLM graduates must verify bar-admission rules for their target state."},
        ],
        "sources": [
            {"label": "BU Law — LLM in American Law", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/american-law/"},
            {"label": "U.S. News — BU School of Law", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-graduate-tax-program": {
        "summary": "BU Law's Graduate Tax Program (LLM in Taxation) is one of the nation's oldest and most recognized tax-law specialties, training attorneys in federal, state, and international tax. Reviewers highlight top tax-law faculty, Boston financial-services recruiting, and national tax-LLM rankings, while noting the program requires a JD or equivalent foreign law degree.",
        "themes": [
            {"label": "Leading tax-law specialty", "sentiment": "positive", "detail": "BU's tax program is widely cited among the top U.S. tax LLMs."},
            {"label": "Boston financial-services market", "sentiment": "positive", "detail": "Graduates place into law firms, accounting firms, and corporate tax roles."},
            {"label": "Requires prior legal degree", "sentiment": "caution", "detail": "Admission expects a JD or equivalent foreign law credential."},
        ],
        "sources": [
            {"label": "BU Law — Graduate Tax Program", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/taxation/"},
            {"label": "U.S. News — tax law rankings", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/tax-law-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-two-year-master-of-laws-llm-in-american-law": {
        "summary": "BU Law's two-year LLM in American Law provides additional time and English-language support for international lawyers adapting to U.S. legal study. Reviewers value the extended timeline for language and doctrinal mastery, BU Law's LLM community, and Boston legal networking, while noting the extra year adds tuition and opportunity cost.",
        "themes": [
            {"label": "Extended LLM timeline", "sentiment": "positive", "detail": "Two years allow deeper immersion in U.S. legal study and language."},
            {"label": "International lawyer community", "sentiment": "positive", "detail": "BU Law hosts a large, diverse LLM student body."},
            {"label": "Extra year of cost", "sentiment": "caution", "detail": "The two-year format adds tuition beyond the one-year LLM."},
        ],
        "sources": [
            {"label": "BU Law — Two-Year LLM American Law", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/american-law/two-year-program/"},
            {"label": "U.S. News — BU School of Law", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-two-year-master-of-laws-llm-in-banking-financial-law": {
        "summary": "BU Law's two-year LLM in Banking & Financial Law gives international and domestic lawyers extended training in securities, banking regulation, and financial transactions — building on BU's top-ranked financial-law faculty. Reviewers cite the specialty's national reputation and Boston asset-management access, while noting the two-year format suits students needing additional language or doctrinal preparation.",
        "themes": [
            {"label": "Top financial-law LLM", "sentiment": "positive", "detail": "BU Law's banking and financial-law program is nationally recognized."},
            {"label": "Extended preparation time", "sentiment": "positive", "detail": "Two years support deeper mastery for international students."},
            {"label": "Requires legal background", "sentiment": "caution", "detail": "The LLM expects prior legal training."},
        ],
        "sources": [
            {"label": "BU Law — Two-Year Banking & Financial Law LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/banking-financial-law/two-year-program/"},
            {"label": "U.S. News — BU School of Law", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-accelerated-llm-in-banking-financial-law": {
        "summary": "BU Law's accelerated LLM in Banking & Financial Law lets JD students or qualified lawyers earn the financial-law LLM in a compressed timeline alongside or after their JD. Reviewers highlight BU's specialty rankings, Boston finance recruiting, and efficient dual-credential path, while noting the accelerated pace is demanding.",
        "themes": [
            {"label": "Compressed financial-law LLM", "sentiment": "positive", "detail": "Qualified students complete the specialty LLM on an accelerated schedule."},
            {"label": "National financial-law reputation", "sentiment": "positive", "detail": "BU Law's banking and securities faculty are widely cited."},
            {"label": "Intensive schedule", "sentiment": "caution", "detail": "The accelerated format requires heavy courseload management."},
        ],
        "sources": [
            {"label": "BU Law — Accelerated Banking & Financial Law LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/banking-financial-law/accelerated-program/"},
            {"label": "U.S. News — BU School of Law", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-international-relations-international-relations-ma-mba": {
        "summary": "BU's MA/MBA in International Relations combines GRS international-affairs training with Questrom's MBA for careers in global business, diplomacy, and international consulting. Reviewers praise BU's Pardee School legacy, Boston's international NGO and consulting presence, and the dual credential, while noting the extended timeline of completing both degrees.",
        "themes": [
            {"label": "International affairs plus MBA", "sentiment": "positive", "detail": "Students blend IR theory and regional expertise with business fundamentals."},
            {"label": "Boston global-affairs ecosystem", "sentiment": "positive", "detail": "Internships span NGOs, consulting, and multinational firms."},
            {"label": "Dual-degree duration", "sentiment": "caution", "detail": "MA and MBA requirements extend total time in school."},
        ],
        "sources": [
            {"label": "Pardee School — MA/MBA International Relations", "url": "https://www.bu.edu/pardee/academics/graduate-programs/ma-mba/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sha-bs-in-hospitality-communication": {
        "summary": "BU's BS in Hospitality Communication at the School of Hospitality Administration blends hospitality management with communication skills for hotel, event, and tourism leadership. Reviewers cite SHA's top-5 U.S. hospitality ranking, required industry internships in Boston and beyond, and the communication focus for marketing and guest-experience roles, while noting the program is niche compared with general business degrees.",
        "themes": [
            {"label": "Top-ranked hospitality school", "sentiment": "positive", "detail": "SHA consistently ranks among the leading U.S. hospitality programs."},
            {"label": "Communication plus hospitality", "sentiment": "positive", "detail": "Curriculum combines guest experience, marketing, and hospitality operations."},
            {"label": "Niche industry focus", "sentiment": "mixed", "detail": "The degree targets hospitality and tourism rather than general business."},
        ],
        "sources": [
            {"label": "BU School of Hospitality Administration", "url": "https://www.bu.edu/hospitality/"},
            {"label": "U.S. News — hospitality management", "url": "https://www.usnews.com/best-colleges/rankings/business-hospitality-management"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-busm-md-phd-combined-degree": {
        "summary": "BU's MD/PhD program trains physician-scientists through the Chobanian & Avedisian School of Medicine with research across biomedical sciences, neuroscience, and engineering. Reviewers cite funded MSTP-style support, NEIDL and hospital research access, and Boston's biomedical cluster, while warning of the long training timeline typical of dual-degree physician-scientist programs.",
        "themes": [
            {"label": "Physician-scientist training", "sentiment": "positive", "detail": "Students complete medical school alongside doctoral research training."},
            {"label": "Biomedical research ecosystem", "sentiment": "positive", "detail": "Medical Campus labs span infectious disease, neuroscience, and engineering."},
            {"label": "Long training path", "sentiment": "caution", "detail": "MD/PhD programs typically require 7–8+ years of study."},
        ],
        "sources": [
            {"label": "BU Medicine — MD/PhD", "url": "https://www.bumc.bu.edu/busm/education/md-programs/dual-degree-programs/md-phd/"},
            {"label": "U.S. News — Best Medical Schools (Research)", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/boston-university-04086"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-bamph-program": {
        "summary": "BU's combined BA-to-MPH program lets CAS undergraduates progress into the accredited School of Public Health MPH, leveraging BU's top-10 SPH ranking and Boston public-health employers. Reviewers value the streamlined public-health career path and practicum network, while noting admission to the MPH portion requires meeting SPH prerequisites and GPA standards.",
        "themes": [
            {"label": "Undergraduate-to-MPH pipeline", "sentiment": "positive", "detail": "CAS students can enter the accredited SPH MPH on an accelerated path."},
            {"label": "Top-10 SPH destination", "sentiment": "positive", "detail": "The MPH leverages BU SPH's national reputation and practicum network."},
            {"label": "Selective MPH admission", "sentiment": "caution", "detail": "Students must meet SPH admission standards for the graduate portion."},
        ],
        "sources": [
            {"label": "BU SPH — BA/MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph-ms-phd/ba-mph/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-economics-ba-ma": {
        "summary": "BU's combined BA/MA in Economics lets CAS undergraduates earn a master's in economics with an accelerated fifth year, building on a department known for empirical and policy-oriented research. Reviewers praise the quantitative training, faculty strength in econometrics and policy, and recruiting into consulting, finance, and PhD pipelines, while noting the MA year requires strong math preparation.",
        "themes": [
            {"label": "Accelerated economics MA", "sentiment": "positive", "detail": "Qualified undergraduates complete the MA in a fifth year."},
            {"label": "Quantitative and policy strength", "sentiment": "positive", "detail": "Faculty research spans econometrics, labor, and development economics."},
            {"label": "Math-intensive MA year", "sentiment": "caution", "detail": "Graduate econometrics and theory courses demand strong quantitative skills."},
        ],
        "sources": [
            {"label": "BU Economics — BA/MA", "url": "https://www.bu.edu/econ/undergraduate/combined-ba-ma/"},
            {"label": "BU Department of Economics", "url": "https://www.bu.edu/econ/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-materials-science-engineering-phd": {
        "summary": "BU's PhD in Materials Science & Engineering trains researchers in nanomaterials, biomaterials, photonics, and energy storage within a Carnegie R1 engineering college on the Charles River campus. Reviewers cite funded assistantships, the Photonics Center and NEIDL-adjacent materials labs, and placement into academia and Boston-area biotech, while noting the five-year-plus dissertation path is highly selective.",
        "themes": [
            {"label": "Materials research breadth", "sentiment": "positive", "detail": "Faculty span nanomaterials, polymers, photonics, and biomedical materials."},
            {"label": "Funded doctoral training", "sentiment": "positive", "detail": "Admitted PhD students typically receive tuition support and research stipends."},
            {"label": "Long, selective path", "sentiment": "caution", "detail": "The PhD requires multi-year coursework, qualifying exams, and dissertation research."},
        ],
        "sources": [
            {"label": "BU Materials Science & Engineering — PhD", "url": "https://www.bu.edu/eng/academics/departments-and-divisions/materials-science-engineering/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-eng-systems-engineering-phd": {
        "summary": "BU's PhD in Systems Engineering focuses on complex engineered systems, reliability, and decision analysis within the College of Engineering's interdisciplinary research environment. Reviewers highlight ties to defense and aerospace employers, funded assistantships, and faculty in reliability and systems design, while noting the program is smaller and more specialized than traditional departmental PhDs.",
        "themes": [
            {"label": "Systems and reliability focus", "sentiment": "positive", "detail": "Research spans systems design, reliability engineering, and decision analysis."},
            {"label": "Industry-relevant training", "sentiment": "positive", "detail": "Graduates pursue roles in aerospace, defense, and complex-systems consulting."},
            {"label": "Smaller specialized cohort", "sentiment": "mixed", "detail": "The program is niche compared with larger departmental PhD pipelines."},
        ],
        "sources": [
            {"label": "BU Systems Engineering — PhD", "url": "https://www.bu.edu/eng/academics/departments-and-divisions/systems-engineering/"},
            {"label": "BU College of Engineering", "url": "https://www.bu.edu/eng/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-economics-ma-economic-policy": {
        "summary": "BU's MA in Economic Policy (GRS) trains practitioners in applied econometrics, policy analysis, and program evaluation for government, NGOs, and think tanks. Reviewers praise the quantitative core, Boston policy-employer access, and the department's empirical research tradition, while noting the one-year format is intensive and math-heavy.",
        "themes": [
            {"label": "Applied policy economics", "sentiment": "positive", "detail": "Coursework emphasizes econometrics, policy evaluation, and empirical methods."},
            {"label": "Boston policy market", "sentiment": "positive", "detail": "Graduates recruit into government, consulting, and nonprofit policy roles."},
            {"label": "Intensive quantitative year", "sentiment": "caution", "detail": "The one-year MA requires strong math and statistics preparation."},
        ],
        "sources": [
            {"label": "BU Economics — MA Economic Policy", "url": "https://www.bu.edu/econ/graduate/ma-economic-policy/"},
            {"label": "BU Department of Economics", "url": "https://www.bu.edu/econ/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-economics-ma-global-development-economics": {
        "summary": "BU's MA in Global Development Economics (GRS) combines microeconomics, development policy, and field-research methods for careers in international development and global health economics. Reviewers cite faculty expertise in development and health economics, ties to BU's global-health programs, and recruiting into NGOs and multilateral agencies, while noting quantitative methods coursework is demanding.",
        "themes": [
            {"label": "Development economics specialty", "sentiment": "positive", "detail": "Training spans development microeconomics, policy, and empirical field methods."},
            {"label": "Global-health and NGO pathways", "sentiment": "positive", "detail": "Graduates pursue roles in development agencies, NGOs, and global health."},
            {"label": "Quantitative methods load", "sentiment": "caution", "detail": "Econometrics and empirical-methods courses require prior statistics training."},
        ],
        "sources": [
            {"label": "BU Economics — MA Global Development Economics", "url": "https://www.bu.edu/econ/graduate/ma-global-development-economics/"},
            {"label": "BU Department of Economics", "url": "https://www.bu.edu/econ/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-economics-ma-phd": {
        "summary": "BU's PhD in Economics (GRS) is a research doctorate training scholars in econometrics, macroeconomics, labor, and development for academia and quantitative research roles. Reviewers highlight funded assistantships, faculty placement into research universities, and Boston's finance and policy ecosystem, while noting the multi-year path is highly competitive.",
        "themes": [
            {"label": "Research-focused economics doctorate", "sentiment": "positive", "detail": "Training spans theory, econometrics, and field-specific dissertation research."},
            {"label": "Funded doctoral support", "sentiment": "positive", "detail": "Admitted students typically receive tuition remission and teaching/research assistantships."},
            {"label": "Highly competitive admission", "sentiment": "caution", "detail": "The PhD admits a small cohort each year with strong quantitative backgrounds."},
        ],
        "sources": [
            {"label": "BU Economics — PhD", "url": "https://www.bu.edu/econ/graduate/phd/"},
            {"label": "BU Department of Economics", "url": "https://www.bu.edu/econ/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-grs-earth-environment-ma-in-energy-environment-mba-dual-degree-program": {
        "summary": "BU's dual MA in Energy & Environment and MBA (Questrom) trains leaders who combine environmental science with business strategy for energy, sustainability, and climate-transition roles. Reviewers value the rare science-plus-MBA credential, Questrom's sustainability themes, and Boston clean-energy employers, while noting the dual degree extends timeline and tuition beyond either program alone.",
        "themes": [
            {"label": "Energy science plus MBA", "sentiment": "positive", "detail": "Graduates bridge environmental science, policy, and business leadership."},
            {"label": "Sustainability-focused Questrom", "sentiment": "positive", "detail": "Questrom integrates energy and sustainability themes across the MBA curriculum."},
            {"label": "Extended dual-degree timeline", "sentiment": "caution", "detail": "Completing both the MA and MBA adds years and cost beyond a single degree."},
        ],
        "sources": [
            {"label": "BU Earth & Environment — Energy & Environment MBA Dual", "url": "https://www.bu.edu/earth/graduate/ma-energy-environment-mba/"},
            {"label": "Questrom School of Business", "url": "https://www.bu.edu/questrom/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-economics-ba-econ-math-ma": {
        "summary": "BU's combined BA in Economics & Mathematics / MA in Economics lets quantitatively strong undergraduates earn a master's with an accelerated fifth year. Reviewers praise the dual math-economics foundation, preparation for PhD economics and quant finance, and department faculty strength, while noting the combined track requires advanced calculus and proof-based math from the start.",
        "themes": [
            {"label": "Math-economics combined foundation", "sentiment": "positive", "detail": "Students build rigorous training in both mathematics and economic theory."},
            {"label": "PhD and quant-finance pipeline", "sentiment": "positive", "detail": "Graduates pursue doctoral study and quantitative roles in finance and consulting."},
            {"label": "Heavy math prerequisites", "sentiment": "caution", "detail": "The track demands strong calculus, linear algebra, and proof skills early."},
        ],
        "sources": [
            {"label": "BU Economics — BA/MA", "url": "https://www.bu.edu/econ/undergraduate/combined-ba-ma/"},
            {"label": "BU Department of Mathematics & Statistics", "url": "https://www.bu.edu/math/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-economics-ba-mathematics": {
        "summary": "BU's combined BA in Economics and Mathematics is a rigorous double-major path for students pursuing quantitative economics, data science, or graduate study. Reviewers highlight the department's empirical research culture, flexibility to combine with CS or statistics, and recruiting into consulting and finance, while noting course sequencing across two quantitative departments requires careful planning.",
        "themes": [
            {"label": "Quantitative double major", "sentiment": "positive", "detail": "Students combine economic theory with advanced mathematics coursework."},
            {"label": "Graduate-school preparation", "sentiment": "positive", "detail": "The combination prepares students for economics PhD and quant careers."},
            {"label": "Demanding course load", "sentiment": "caution", "detail": "Fulfilling both majors' requirements in four years requires early planning."},
        ],
        "sources": [
            {"label": "BU Economics — Undergraduate", "url": "https://www.bu.edu/econ/undergraduate/"},
            {"label": "BU Department of Mathematics & Statistics", "url": "https://www.bu.edu/math/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-physics-ba-in-physics-computer-science": {
        "summary": "BU's combined BA in Physics and Computer Science trains students at the intersection of physical modeling, computation, and data-intensive science within CAS. Reviewers cite access to research labs, preparation for computational physics and tech roles, and Boston's science-and-tech hiring, while noting the dual major's math and programming requirements are substantial.",
        "themes": [
            {"label": "Physics-computation intersection", "sentiment": "positive", "detail": "Coursework spans classical and modern physics with CS and numerical methods."},
            {"label": "Research and tech pathways", "sentiment": "positive", "detail": "Graduates pursue computational science, simulation, and software engineering roles."},
            {"label": "Heavy STEM workload", "sentiment": "caution", "detail": "Both majors require advanced math, physics, and programming courses."},
        ],
        "sources": [
            {"label": "BU Department of Physics", "url": "https://www.bu.edu/physics/"},
            {"label": "BU Department of Computer Science", "url": "https://www.bu.edu/cs/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-mathematics-statistics-ba-mathematics-computer-science": {
        "summary": "BU's combined BA in Mathematics and Computer Science is a flagship quantitative double major preparing students for software engineering, data science, and theoretical CS graduate study. Reviewers praise the rigor of both departments, CDS cross-registration, and Boston tech recruiting, while noting upper-level proof-based math and systems courses compete for time.",
        "themes": [
            {"label": "Rigorous math-CS combination", "sentiment": "positive", "detail": "Students build foundations in discrete math, algorithms, and advanced calculus."},
            {"label": "Tech and graduate-school pipeline", "sentiment": "positive", "detail": "Graduates recruit into software, quant finance, and CS graduate programs."},
            {"label": "Competing advanced requirements", "sentiment": "caution", "detail": "Both majors' upper-level courses require careful scheduling."},
        ],
        "sources": [
            {"label": "BU Department of Mathematics & Statistics", "url": "https://www.bu.edu/math/"},
            {"label": "BU Department of Computer Science", "url": "https://www.bu.edu/cs/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-met-computer-science-bs-accelerated": {
        "summary": "MET's Accelerated Bachelor of Science in Computer Science lets working adults complete a BU CS bachelor's on an evening/online-friendly schedule. Reviewers value the BU credential, flexible pacing for career changers, and access to the same CS curriculum as residential students, while noting the part-time path takes longer than a traditional four-year program and tuition is per credit.",
        "themes": [
            {"label": "BU CS degree for working adults", "sentiment": "positive", "detail": "Evening and online options let professionals earn a BU bachelor's in CS."},
            {"label": "Career-changer friendly", "sentiment": "positive", "detail": "The accelerated format suits professionals transitioning into tech."},
            {"label": "Longer part-time timeline", "sentiment": "caution", "detail": "Part-time study extends completion beyond a standard four-year schedule."},
        ],
        "sources": [
            {"label": "MET — BS Computer Science (Accelerated)", "url": "https://www.bu.edu/met/programs/undergraduate/computer-science-bs/"},
            {"label": "BU Metropolitan College", "url": "https://www.bu.edu/met/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-mph-sex-sexuality-and-gender": {
        "summary": "BU SPH's sex, sexuality, and gender MPH concentration is a distinctive public-health specialty addressing LGBTQ+ health, reproductive justice, and gender-based disparities. Reviewers highlight the unique interdisciplinary curriculum, faculty in sexual-health research, and advocacy-oriented career paths, while noting the niche focus may not suit students seeking broad epidemiology training.",
        "themes": [
            {"label": "Distinctive sexual-health focus", "sentiment": "positive", "detail": "Coursework addresses LGBTQ+ health, reproductive justice, and gender disparities."},
            {"label": "Advocacy and research pathways", "sentiment": "positive", "detail": "Graduates work in nonprofits, health departments, and sexual-health research."},
            {"label": "Niche vs. broad epi training", "sentiment": "mixed", "detail": "The concentration is specialized compared with general epidemiology tracks."},
        ],
        "sources": [
            {"label": "BU SPH — Sex, Sexuality & Gender MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/sex-sexuality-and-gender/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-programs-health-communication-and-promotion": {
        "summary": "BU SPH's health communication and promotion MPH concentration trains practitioners in health messaging, social marketing, and community engagement — leveraging COM's journalism heritage and SPH's top-10 ranking. Reviewers praise the media-and-public-health blend, Boston health-communications employers, and applied practicum work, while noting the concentration is less quant-heavy than epidemiology tracks.",
        "themes": [
            {"label": "Health communications specialty", "sentiment": "positive", "detail": "Training spans health messaging, social marketing, and community outreach."},
            {"label": "COM-SPH interdisciplinary blend", "sentiment": "positive", "detail": "BU's journalism school heritage strengthens media-focused public-health training."},
            {"label": "Less quantitative than epi", "sentiment": "mixed", "detail": "The track emphasizes communications skills over biostatistics depth."},
        ],
        "sources": [
            {"label": "BU SPH — Health Communication & Promotion MPH", "url": "https://www.bu.edu/sph/education/degrees-and-programs/ma-mph/ms-phd/health-communication-and-promotion/"},
            {"label": "BU School of Public Health", "url": "https://www.bumc.bu.edu/sph/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-social-work-and-public-health": {
        "summary": "BU's MSW/MPH dual degree pairs the nationally ranked School of Social Work with the top-10 School of Public Health for community-health and policy leadership. Reviewers value the combined clinical-plus-population credential, Boston nonprofit and health-agency recruiting, and field-placement breadth, while noting the dual program adds a year of coursework and tuition.",
        "themes": [
            {"label": "Clinical plus population health", "sentiment": "positive", "detail": "Graduates combine social-work practice with public-health policy skills."},
            {"label": "Top-ranked partner schools", "sentiment": "positive", "detail": "SSW and SPH both rank among the nation's leading professional schools."},
            {"label": "Extended dual timeline", "sentiment": "caution", "detail": "Earning both the MSW and MPH requires additional semesters beyond either alone."},
        ],
        "sources": [
            {"label": "BU SSW — MSW/MPH Dual Degree", "url": "https://www.bu.edu/ssw/academics/msw/dual-degrees/msw-mph/"},
            {"label": "U.S. News — social work rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-medical-sciences-and-public-health": {
        "summary": "BU's MS in Medical Sciences / MPH dual degree prepares students for physician-assistant, medical-school, and public-health careers by combining biomedical science with population-health training. Reviewers cite the Medical Campus research environment, SPH's top-10 ranking, and a structured pre-health pathway, while noting the dual credential extends study beyond a single master's.",
        "themes": [
            {"label": "Biomedical science plus public health", "sentiment": "positive", "detail": "Students combine medical-sciences coursework with MPH foundations."},
            {"label": "Pre-health and policy pathways", "sentiment": "positive", "detail": "Graduates pursue clinical programs, health policy, and research roles."},
            {"label": "Additional semesters required", "sentiment": "caution", "detail": "The dual degree adds coursework beyond either program alone."},
        ],
        "sources": [
            {"label": "BU GMS — Medical Sciences / MPH", "url": "https://www.bumc.bu.edu/gms/academics/ms-programs/medical-sciences/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sph-ms-in-genetic-counseling-master-of-public-health-ms-mph": {
        "summary": "BU's MS in Genetic Counseling / MPH dual degree is a rare credential combining clinical genetics counseling with population-health training at a top-10 SPH. Reviewers highlight ACGC-accredited genetic-counseling training, Boston children's-hospital clinical sites, and the added public-health breadth, while noting admission is highly competitive and clinical rotations are time-intensive.",
        "themes": [
            {"label": "Genetic counseling plus MPH", "sentiment": "positive", "detail": "Graduates combine clinical genetics expertise with public-health policy skills."},
            {"label": "Boston clinical training sites", "sentiment": "positive", "detail": "Rotations include major Boston hospitals and genetics clinics."},
            {"label": "Competitive, intensive training", "sentiment": "caution", "detail": "Clinical rotations and dual-degree coursework demand significant time commitment."},
        ],
        "sources": [
            {"label": "BU GMS — Genetic Counseling / MPH", "url": "https://www.bumc.bu.edu/gms/academics/ms-programs/genetic-counseling/"},
            {"label": "U.S. News — public health rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-ssw-macro-social-work-practice": {
        "summary": "BU's Macro Social Work Practice concentration within the MSW trains leaders in community organizing, policy advocacy, and nonprofit management. Reviewers cite SSW's top-10 ranking, Boston's nonprofit sector as a field-placement hub, and the macro track's policy focus, while noting macro placements can be less structured than clinical ones.",
        "themes": [
            {"label": "Policy and community leadership", "sentiment": "positive", "detail": "Training spans organizing, advocacy, and nonprofit management."},
            {"label": "Top-ranked SSW", "sentiment": "positive", "detail": "BU SSW ranks among the nation's leading schools of social work."},
            {"label": "Less structured than clinical", "sentiment": "mixed", "detail": "Macro field placements vary more than standardized clinical rotations."},
        ],
        "sources": [
            {"label": "BU SSW — Macro Practice", "url": "https://www.bu.edu/ssw/academics/msw/"},
            {"label": "U.S. News — social work rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-ssw-phd-in-social-work": {
        "summary": "BU's PhD in Social Work trains scholar-practitioners in social-welfare policy, intervention research, and academic leadership within a top-10 SSW. Reviewers highlight funded assistantships, faculty expertise in child welfare and health disparities, and placement into research universities, while noting the multi-year dissertation path is selective.",
        "themes": [
            {"label": "Social-work research doctorate", "sentiment": "positive", "detail": "Training spans policy research, intervention science, and dissertation scholarship."},
            {"label": "Funded doctoral support", "sentiment": "positive", "detail": "Admitted students typically receive tuition support and research assistantships."},
            {"label": "Selective, long path", "sentiment": "caution", "detail": "The PhD requires years of coursework and original dissertation research."},
        ],
        "sources": [
            {"label": "BU SSW — PhD in Social Work", "url": "https://www.bu.edu/ssw/academics/phd/"},
            {"label": "U.S. News — social work rankings", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-ssw-dual-degree-in-theology-and-social-work": {
        "summary": "BU's MSW/MTS dual degree pairs the School of Social Work with the School of Theology for faith-informed clinical and community practice. Reviewers value the unique integration of theological ethics with social-work training, field placements in faith-based agencies, and SSW's top-10 ranking, while noting the dual program extends the MSW timeline.",
        "themes": [
            {"label": "Faith-informed social work", "sentiment": "positive", "detail": "Students integrate theological ethics with clinical and community practice."},
            {"label": "Faith-based field placements", "sentiment": "positive", "detail": "Practicum sites include churches, faith-based nonprofits, and community agencies."},
            {"label": "Extended dual timeline", "sentiment": "caution", "detail": "The MTS coursework adds semesters beyond the MSW alone."},
        ],
        "sources": [
            {"label": "BU SSW — MSW/MTS Dual Degree", "url": "https://www.bu.edu/ssw/academics/msw/dual-degrees/msw-mts/"},
            {"label": "BU School of Theology", "url": "https://www.bu.edu/sth/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-ssw-dual-degree-programs-in-social-work-and-education": {
        "summary": "BU's MSW/EdD dual degree combines clinical social work with educational leadership for roles in school social work, student services, and education policy. Reviewers cite SSW's top-10 ranking, the Wheelock College of Education partnership, and school-district field placements, while noting the EdD adds dissertation work beyond the MSW.",
        "themes": [
            {"label": "School social work leadership", "sentiment": "positive", "detail": "Graduates lead student services, counseling, and education-policy initiatives."},
            {"label": "SSW-Wheelock partnership", "sentiment": "positive", "detail": "BU's education and social-work schools collaborate on the dual credential."},
            {"label": "EdD dissertation commitment", "sentiment": "caution", "detail": "The education doctorate adds research requirements beyond the MSW."},
        ],
        "sources": [
            {"label": "BU SSW — MSW/EdD Dual Degree", "url": "https://www.bu.edu/ssw/academics/msw/dual-degrees/"},
            {"label": "BU Wheelock College of Education", "url": "https://www.bu.edu/wheelock/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-accelerated-llm-in-taxation": {
        "summary": "BU Law's accelerated LLM in Taxation lets qualified JD students or practicing attorneys complete the nationally ranked tax LLM on a compressed timeline. Reviewers highlight BU's top tax-law specialty, Boston financial-services recruiting, and efficient credential stacking, while noting the accelerated pace is demanding for students also completing a JD.",
        "themes": [
            {"label": "Compressed tax LLM", "sentiment": "positive", "detail": "Qualified students earn the tax specialty LLM on an accelerated schedule."},
            {"label": "Top tax-law program", "sentiment": "positive", "detail": "BU's Graduate Tax Program ranks among the nation's leading tax LLMs."},
            {"label": "Demanding alongside JD", "sentiment": "caution", "detail": "Completing the accelerated LLM while finishing a JD requires heavy courseload management."},
        ],
        "sources": [
            {"label": "BU Law — Accelerated Tax LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/taxation/accelerated-program/"},
            {"label": "U.S. News — tax law rankings", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/tax-law-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-two-year-master-of-laws-llm-in-intellectual-property-information-law": {
        "summary": "BU Law's two-year LLM in Intellectual Property & Information Law gives international lawyers extended training in patents, copyrights, and technology law — building on BU's nationally recognized IP faculty. Reviewers cite the specialty's reputation, Boston tech-and-biotech legal market, and additional time for language mastery, while noting the extra year adds tuition.",
        "themes": [
            {"label": "IP and technology-law specialty", "sentiment": "positive", "detail": "Coursework spans patents, copyrights, trademarks, and information law."},
            {"label": "Boston tech legal market", "sentiment": "positive", "detail": "Graduates place into IP practices serving biotech and technology firms."},
            {"label": "Two-year tuition cost", "sentiment": "caution", "detail": "The extended format adds a year of tuition beyond the one-year LLM."},
        ],
        "sources": [
            {"label": "BU Law — Two-Year IP LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/intellectual-property/two-year-program/"},
            {"label": "U.S. News — BU School of Law", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-two-year-master-of-laws-llm-in-tax-law": {
        "summary": "BU Law's two-year LLM in Tax Law (MSL-TAX pathway) provides extended training for international and domestic students pursuing the nation's top-ranked tax specialty. Reviewers highlight leading tax faculty, Boston accounting-and-law-firm recruiting, and the two-year format's language support, while noting admission requires a legal or accounting background.",
        "themes": [
            {"label": "Extended tax-law training", "sentiment": "positive", "detail": "Two years allow deeper mastery of federal, state, and international tax."},
            {"label": "National tax specialty leader", "sentiment": "positive", "detail": "BU's Graduate Tax Program is widely cited among top U.S. tax programs."},
            {"label": "Requires legal/accounting background", "sentiment": "caution", "detail": "Admission expects prior legal or accounting training."},
        ],
        "sources": [
            {"label": "BU Law — Two-Year Tax LLM", "url": "https://www.bu.edu/law/academics/degree-programs/llm-programs/taxation/two-year-program/"},
            {"label": "U.S. News — tax law rankings", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/tax-law-rankings"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-jdma-ir": {
        "summary": "BU Law's JD/MA in International Relations dual degree trains attorneys with deep expertise in global governance, diplomacy, and international business law. Reviewers value the Pardee School partnership, combined legal-and-policy credential, and recruiting into government and international organizations, while noting the dual program extends the JD timeline by a year.",
        "themes": [
            {"label": "Law plus international relations", "sentiment": "positive", "detail": "Students combine JD training with Pardee School IR coursework."},
            {"label": "Global governance pathways", "sentiment": "positive", "detail": "Graduates pursue roles in government, NGOs, and international business law."},
            {"label": "Extended JD timeline", "sentiment": "caution", "detail": "The MA adds a year of coursework beyond the three-year JD."},
        ],
        "sources": [
            {"label": "BU Law — JD/MA International Relations", "url": "https://www.bu.edu/law/academics/degree-programs/jd-program/dual-degree-programs/jd-ma-international-relations/"},
            {"label": "BU Pardee School of Global Studies", "url": "https://www.bu.edu/pardee/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-jdma-history": {
        "summary": "BU Law's JD/MA in History dual degree pairs legal training with historical scholarship for careers in legal history, academia, and public-policy research. Reviewers cite CAS history faculty strength, the combined research credential, and preparation for academic legal-history roles, while noting the dual degree adds a year beyond the JD.",
        "themes": [
            {"label": "Legal history scholarship", "sentiment": "positive", "detail": "Students combine JD training with graduate historical research methods."},
            {"label": "Academic and policy research", "sentiment": "positive", "detail": "Graduates pursue legal-history scholarship and policy-research roles."},
            {"label": "Additional year of study", "sentiment": "caution", "detail": "The MA adds coursework and thesis work beyond the three-year JD."},
        ],
        "sources": [
            {"label": "BU Law — JD/MA History", "url": "https://www.bu.edu/law/academics/degree-programs/jd-program/dual-degree-programs/jd-ma-history/"},
            {"label": "BU Department of History", "url": "https://www.bu.edu/history/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-law-jdma-philosophy": {
        "summary": "BU Law's JD/MA in Philosophy dual degree integrates legal reasoning with philosophical ethics and jurisprudence for students pursuing legal academia, public-interest law, and policy ethics. Reviewers highlight CAS philosophy faculty, the combined analytic-training credential, and preparation for legal-scholarship roles, while noting the dual program extends the JD by a year.",
        "themes": [
            {"label": "Law and philosophical ethics", "sentiment": "positive", "detail": "Students combine JD training with graduate philosophy and jurisprudence."},
            {"label": "Legal scholarship preparation", "sentiment": "positive", "detail": "Graduates pursue academic law, ethics consulting, and public-interest roles."},
            {"label": "Extended timeline", "sentiment": "caution", "detail": "The MA adds a year of graduate philosophy coursework beyond the JD."},
        ],
        "sources": [
            {"label": "BU Law — JD/MA Philosophy", "url": "https://www.bu.edu/law/academics/degree-programs/jd-program/dual-degree-programs/jd-ma-philosophy/"},
            {"label": "BU Department of Philosophy", "url": "https://www.bu.edu/philo/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-gms-biomedical-forensic-sciences": {
        "summary": "BU's MS in Biomedical Forensic Sciences (GMS) trains practitioners in forensic biology, chemistry, and crime-scene investigation within BU's Medical Campus research environment. Reviewers cite the program's FEPAC-aligned curriculum, Boston-area crime-lab practicum sites, and strong job placement in forensic laboratories, while noting the field requires meticulous lab work and emotional resilience.",
        "themes": [
            {"label": "Forensic science laboratory training", "sentiment": "positive", "detail": "Coursework spans forensic biology, chemistry, and crime-scene analysis."},
            {"label": "Crime-lab career placement", "sentiment": "positive", "detail": "Graduates place into forensic laboratories and law-enforcement agencies."},
            {"label": "Demanding field work", "sentiment": "caution", "detail": "Forensic casework requires precision and resilience with sensitive evidence."},
        ],
        "sources": [
            {"label": "BU GMS — Biomedical Forensic Sciences", "url": "https://www.bumc.bu.edu/gms/academics/ms-programs/biomedical-forensic-sciences/"},
            {"label": "BU Graduate Medical Sciences", "url": "https://www.bumc.bu.edu/gms/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-gms-mental-health-counseling-behavioral-medicine-program-ma": {
        "summary": "BU's MA in Mental Health Counseling & Behavioral Medicine (GMS) trains licensed-eligible counselors with a biomedical understanding of mental health within the Medical Campus. Reviewers praise the clinical training model, Boston hospital and community-agency placements, and CACREP-aligned curriculum, while noting practicum hours and licensure requirements extend beyond graduation.",
        "themes": [
            {"label": "Clinical counseling with biomedical focus", "sentiment": "positive", "detail": "Training integrates psychotherapy with behavioral-medicine science."},
            {"label": "Boston clinical placements", "sentiment": "positive", "detail": "Practicum sites include hospitals, clinics, and community mental-health agencies."},
            {"label": "Post-graduation licensure hours", "sentiment": "caution", "detail": "State licensure requires supervised clinical hours beyond the degree."},
        ],
        "sources": [
            {"label": "BU GMS — Mental Health Counseling MA", "url": "https://www.bumc.bu.edu/gms/academics/ma-programs/mental-health-counseling-behavioral-medicine/"},
            {"label": "BU Graduate Medical Sciences", "url": "https://www.bumc.bu.edu/gms/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-gms-virology-immunology-microbiology-program": {
        "summary": "BU's PhD and MD/PhD in Virology, Immunology & Microbiology (GMS) leverages the Medical Campus and NEIDL-adjacent research for training in infectious disease, immunology, and microbial pathogenesis. Reviewers cite funded assistantships, NEIDL proximity, and placement into academia and biotech, while noting biosafety training and competitive admission.",
        "themes": [
            {"label": "Infectious-disease research training", "sentiment": "positive", "detail": "Research spans virology, immunology, and microbial pathogenesis."},
            {"label": "NEIDL research ecosystem", "sentiment": "positive", "detail": "BU's National Emerging Infectious Diseases Laboratories support related research."},
            {"label": "Competitive, biosafety-intensive", "sentiment": "caution", "detail": "Some research requires biosafety training and selective lab access."},
        ],
        "sources": [
            {"label": "BU GMS — Virology, Immunology & Microbiology", "url": "https://www.bumc.bu.edu/gms/academics/phd-programs/virology-immunology-microbiology/"},
            {"label": "National Emerging Infectious Diseases Laboratories", "url": "https://www.bu.edu/neidl/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-sdm-dental-public-health-ms": {
        "summary": "BU's MS in Dental Public Health (Goldman School of Dental Medicine) trains dentists and public-health professionals in population oral-health policy, epidemiology, and community programs. Reviewers highlight the accredited dental-school setting, Boston public-health agency partnerships, and preparation for academic and health-department leadership, while noting the program expects a dental or public-health background.",
        "themes": [
            {"label": "Population oral-health leadership", "sentiment": "positive", "detail": "Training spans oral-health epidemiology, policy, and community programs."},
            {"label": "Accredited dental-school context", "sentiment": "positive", "detail": "The program sits within BU's accredited Goldman School of Dental Medicine."},
            {"label": "Requires dental/PH background", "sentiment": "caution", "detail": "Admission expects prior dental or public-health training."},
        ],
        "sources": [
            {"label": "BU SDM — MS Dental Public Health", "url": "https://www.bu.edu/dental/academics/graduate-programs/dental-public-health/"},
            {"label": "BU Goldman School of Dental Medicine", "url": "https://www.bu.edu/dental/"},
        ],
        "disclaimer": "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.",
    },
    "bu-academics-cas-anthropology-anthropology-health-medicine": {
        "summary": "BU's BA in Anthropology with a specialization in Anthropology, Health & Medicine combines medical anthropology with biology and Sargent College health coursework. Reviewers praise the interdisciplinary health-and-culture curriculum, preparation for public-health and pre-med pathways, and CAS anthropology faculty, while noting the specialization adds substantial science requirements beyond the base major.",
        "themes": [
            {"label": 'Medical anthropology specialization', "sentiment": 'positive', "detail": 'Training spans illness, healing systems, and health policy through anthropological methods.'},
            {"label": 'Pre-health and PH pathways', "sentiment": 'positive', "detail": 'Graduates pursue medicine, public health, and health-services research.'},
            {"label": 'Heavy science requirements', "sentiment": 'caution', "detail": 'The specialization requires biology and Sargent coursework beyond core anthropology.'},
        ],
        "sources": [
            {"label": 'BU CAS — Anthropology, Health & Medicine', "url": 'https://www.bu.edu/academics/cas/programs/anthropology/anthropology-health-medicine/'},
            {"label": 'BU Department of Anthropology', "url": 'https://www.bu.edu/anthro/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-mathematics-statistics-ba-in-mathematics-computer-science-ms-in-computer-science": {
        "summary": "BU's combined BA in Mathematics & Computer Science with an MS in Computer Science lets undergraduates stack graduate CS training in a five-year pathway. Reviewers highlight accelerated access to graduate CS coursework, strong theoretical math foundations, and Boston tech placement, while noting the combined program requires careful planning across CAS and CS departments.",
        "themes": [
            {"label": 'Five-year BA/MS CS pathway', "sentiment": 'positive', "detail": 'Students combine undergraduate math-CS with graduate computer-science training.'},
            {"label": 'Strong quantitative foundations', "sentiment": 'positive', "detail": 'Mathematics coursework supports advanced CS theory and systems study.'},
            {"label": 'Cross-department planning', "sentiment": 'caution', "detail": 'Students need advisors in both Mathematics & Statistics and Computer Science.'},
        ],
        "sources": [
            {"label": 'BU CAS — Mathematics & Computer Science BA/MS', "url": 'https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-mathematics-computer-science-ms-in-computer-science/'},
            {"label": 'BU Department of Computer Science', "url": 'https://www.bu.edu/cs/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-mathematics-statistics-ba-in-statistics-computer-science": {
        "summary": "BU's joint BA in Statistics & Computer Science bridges CAS Mathematics & Statistics and the Department of Computer Science for students seeking data-science foundations. Reviewers cite strong quantitative and programming training, Boston tech recruiting, and flexibility for statistics-track math majors, while noting upper-division CS courses must be taken at BU and cannot transfer.",
        "themes": [
            {"label": 'Joint math-statistics and CS major', "sentiment": 'positive', "detail": 'Combines probability, statistics, and core computer-science coursework.'},
            {"label": 'Data-science career preparation', "sentiment": 'positive', "detail": 'Graduates target analytics, tech, and quantitative research roles.'},
            {"label": 'Residency on key CS courses', "sentiment": 'caution', "detail": 'Core upper-division CS courses must be completed at BU.'},
        ],
        "sources": [
            {"label": 'BU CAS — Statistics & Computer Science', "url": 'https://www.bu.edu/academics/cas/programs/mathematics-statistics/ba-in-statistics-computer-science/'},
            {"label": 'BU Department of Computer Science', "url": 'https://www.bu.edu/cs/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-ancient-greek-mfa-in-literary-translation": {
        "summary": "BU's BA in Ancient Greek to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, ancient greek faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'Ancient Greek language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in ancient greek before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA Ancient Greek to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-ancient-greek-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-chinese-mfa-in-literary-translation": {
        "summary": "BU's BA in Chinese to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, chinese faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'Chinese language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in chinese before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA Chinese to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-chinese-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-french-studies-mfa-in-literary-translation": {
        "summary": "BU's BA in French Studies to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, french studies faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'French Studies language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in french studies before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA French Studies to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-french-studies-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-german-mfa-in-literary-translation": {
        "summary": "BU's BA in German to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, german faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'German language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in german before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA German to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-german-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-japanese-mfa-in-literary-translation": {
        "summary": "BU's BA in Japanese to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, japanese faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'Japanese language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in japanese before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA Japanese to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-japanese-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-latin-mfa-in-literary-translation": {
        "summary": "BU's BA in Latin to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, latin faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'Latin language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in latin before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA Latin to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-latin-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-romance-studies-ba-in-spanish-mfa-in-literary-translation": {
        "summary": "BU's BA in Spanish to MFA in Literary Translation gives high-performing undergraduates language-literature training alongside professional translation study. Reviewers praise the accelerated BA-to-MFA structure, spanish faculty depth, and publishing-career preparation, while noting applicants need advanced language proficiency and competitive writing and translation samples.",
        "themes": [
            {"label": 'Spanish language-literature depth', "sentiment": 'positive', "detail": 'Undergraduates build advanced proficiency in spanish before graduate translation work.'},
            {"label": 'Literary Translation MFA integration', "sentiment": 'positive', "detail": 'Students earn the MFA in Literary Translation during their BU tenure.'},
            {"label": 'Selective language proficiency bar', "sentiment": 'caution', "detail": 'Admission requires strong language skills and translation portfolios.'},
        ],
        "sources": [
            {"label": 'BU CAS — BA Spanish to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/romance-studies/ba-in-spanish-mfa-in-literary-translation/'},
            {"label": 'BU Department of Romance Studies', "url": 'https://www.bu.edu/romance/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-cas-world-languages-literatures-ba-in-comparative-literature-mfa-in-literary-translation": {
        "summary": "BU's BA in Comparative Literature-to-MFA in Literary Translation trains high-performing undergraduates in multilingual literary study and professional translation practice within CAS and GRS. Reviewers highlight the accelerated BA-to-MFA pathway, the World Languages & Literatures faculty, and career preparation in publishing and translation, while noting admission is selective and requires strong language proficiency.",
        "themes": [
            {"label": 'Accelerated BA-to-MFA pathway', "sentiment": 'positive', "detail": 'Qualified undergraduates earn the Literary Translation MFA during their BU tenure.'},
            {"label": 'Multilingual literary training', "sentiment": 'positive', "detail": 'Students combine comparative literature with translation theory and practice.'},
            {"label": 'Selective admission', "sentiment": 'caution', "detail": 'Applicants need strong writing samples, translation portfolios, and faculty recommendations.'},
        ],
        "sources": [
            {"label": 'BU — BA Comparative Literature to MFA Literary Translation', "url": 'https://www.bu.edu/academics/cas/programs/world-languages-literatures/ba-in-comparative-literature-mfa-in-literary-translation/'},
            {"label": 'BU Department of World Languages & Literatures', "url": 'https://www.bu.edu/wll/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-anatomy-neurobiology-mdphd": {
        "summary": "BU's MD/PhD in Anatomy & Neurobiology combines Chobanian & Avedisian SOM medical training with doctoral neuroscience research. Reviewers praise funded dual-degree support, the Vesalius teaching module, and placement into academic medicine, while noting the combined program spans seven or more years.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/anatomy-neurobiology/mdphd/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-biochemistry-mdphd": {
        "summary": "BU's MD/PhD in Biochemistry links medical-school training with doctoral research in molecular biochemistry on the Medical Campus. Reviewers highlight NIH-style dual-degree funding, strong basic-science faculty, and academic-medicine placement, while noting admission is highly selective.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/biochemistry/mdphd/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-mdphd-in-bioinformatics": {
        "summary": "BU's MD/PhD in Bioinformatics trains physician-scientists in computational biology and biomedical data science. Reviewers cite the growing bioinformatics research ecosystem, Medical Campus computing resources, and dual-degree funding, while noting the program requires strong quantitative preparation.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/mdphd-in-bioinformatics/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-medical-sciences-dual-degree-masters-program-in-medical-sciences-and-mental-health-counseling-behaviora": {
        "summary": "BU's dual MS in Medical Sciences and MA in Mental Health Counseling & Behavioral Medicine combines biomedical science with clinical counseling training on the Medical Campus. Reviewers highlight the rare science-plus-counseling credential, Boston clinical placements, and licensure-oriented curriculum, while noting the dual program extends study beyond either degree alone.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/medical-sciences/dual-degree-masters-program-in-medical-sciences-and-mental-health-counseling-behavioral-medicine/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-molecular-medicine": {
        "summary": "BU's MD/PhD in Molecular Medicine prepares physician-scientists for translational research bridging basic science and clinical medicine. Reviewers praise BUSM-GMS integration, Boston biotech proximity, and funded dual-degree support, while noting the long training timeline and selective admission.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/molecular-medicine/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-ms-in-biomedical-research-technologies": {
        "summary": "BU's MS in Biomedical Research Technologies (GMS) trains students to operate and apply biomedical research cores — flow cytometry, imaging, proteomics, and bioinformatics. Reviewers praise the one-year practicum model, Medical Campus core facilities, and placement into pharma and academic labs, while noting the program expects prior biochemistry or molecular-biology coursework.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/ms-in-biomedical-research-technologies/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-pathology-laboratory-medicine-ma": {
        "summary": "BU's MA in Pathology & Laboratory Medicine (GMS) provides graduate training in disease mechanisms and laboratory medicine within the Medical Campus. Reviewers cite research-lab access, BUSM-affiliated pathology faculty, and preparation for PhD or clinical-laboratory careers, while noting most students pursue further graduate study.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/pathology-laboratory-medicine/ma/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-gms-pathology-laboratory-medicine-phd": {
        "summary": "BU's MD/PhD in Pathology & Laboratory Medicine trains physician-scientists in disease mechanisms and diagnostic science. Reviewers highlight pathology research labs, clinical exposure through BUSM, and academic-medicine careers, while noting the dual degree requires seven or more years.",
        "themes": [
            {"label": 'Medical Campus research training', "sentiment": 'positive', "detail": 'Programs leverage GMS and BUSM research facilities in Boston.'},
            {"label": 'Biomedical career preparation', "sentiment": 'positive', "detail": 'Graduates place into academia, biotech, and clinical research.'},
            {"label": 'Selective, demanding curriculum', "sentiment": 'caution', "detail": 'Admission expects strong science preparation and sustained research commitment.'},
        ],
        "sources": [
            {"label": 'BU GMS — program page', "url": 'https://www.bu.edu/academics/gms/programs/pathology-laboratory-medicine/phd/'},
            {"label": 'BU Graduate Medical Sciences', "url": 'https://www.bumc.bu.edu/gms/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-grs-history-art-architecture-ma": {
        "summary": "BU's MA in History of Art & Architecture (GRS) trains scholars in architectural and visual-culture history within a major research university. Reviewers cite CFA and GRS faculty strength, Boston's museum and preservation resources, and preparation for PhD study or museum work, while noting funding is limited compared with fully funded doctoral programs.",
        "themes": [
            {"label": 'Art and architectural history training', "sentiment": 'positive', "detail": 'Coursework spans visual culture, architecture, and historiographic methods.'},
            {"label": 'Boston cultural institutions', "sentiment": 'positive', "detail": 'Students access museums, archives, and preservation organizations in the region.'},
            {"label": 'Limited MA funding', "sentiment": 'caution', "detail": 'Most MA students self-fund compared with funded PhD pathways.'},
        ],
        "sources": [
            {"label": 'BU GRS — History of Art & Architecture', "url": 'https://www.bu.edu/academics/grs/programs/history-art-architecture/'},
            {"label": 'BU Department of History of Art & Architecture', "url": 'https://www.bu.edu/arthistory/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-grs-history-art-architecture-phd": {
        "summary": "BU's PhD in History of Art & Architecture prepares dissertation scholars in architectural history, visual culture, and museum studies. Reviewers highlight funded assistantships for admitted students, CFA research resources, and placement into academia and museums, while noting admission is selective and the dissertation timeline spans multiple years.",
        "themes": [
            {"label": 'Doctoral art-history scholarship', "sentiment": 'positive', "detail": 'Training combines historiography, archival research, and dissertation scholarship.'},
            {"label": 'Museum and academic placement', "sentiment": 'positive', "detail": 'Graduates pursue faculty, curatorial, and preservation careers.'},
            {"label": 'Long, selective path', "sentiment": 'caution', "detail": 'The PhD requires years of coursework and original dissertation research.'},
        ],
        "sources": [
            {"label": 'BU GRS — History of Art & Architecture PhD', "url": 'https://www.bu.edu/academics/grs/programs/history-art-architecture/'},
            {"label": 'BU Department of History of Art & Architecture', "url": 'https://www.bu.edu/arthistory/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-grs-sociology-sociology-social-work": {
        "summary": "BU's Interdisciplinary PhD in Sociology & Social Work (GRS/SSW) linked social-science theory with social-welfare research. Reviewers valued the joint SSW-CAS training model and policy-research preparation, while noting the program is no longer admitting new students and applicants should consider the standalone SSW PhD instead.",
        "themes": [
            {"label": 'Sociology-social work integration', "sentiment": 'positive', "detail": 'Doctoral training linked sociological theory with social-welfare research methods.'},
            {"label": 'Policy and clinical research paths', "sentiment": 'positive', "detail": 'Graduates pursued academic and policy-research roles across social work fields.'},
            {"label": 'No longer admitting', "sentiment": 'caution', "detail": 'BU now offers a standalone PhD in Social Work; this joint program is closed to new entrants.'},
        ],
        "sources": [
            {"label": 'BU GRS — Interdisciplinary PhD Sociology & Social Work', "url": 'https://www.bu.edu/academics/grs/programs/sociology/sociology-social-work/'},
            {"label": 'BU School of Social Work — PhD', "url": 'https://www.bu.edu/ssw/academics/phd/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-law-jd-llm-in-international-commercial-and-investment-arbitration-at-paris2": {
        "summary": "BU Law's JD/LLM in International Commercial and Investment Arbitration with Paris II trains students in cross-border dispute resolution. Reviewers highlight the arbitration specialty, Paris-based civil-law training, and international litigation careers, while noting the dual credential requires study in France and competitive admission.",
        "themes": [
            {"label": 'International arbitration specialty', "sentiment": 'positive', "detail": 'Training spans commercial and investment arbitration law and practice.'},
            {"label": 'Paris-based legal study', "sentiment": 'positive', "detail": 'Students earn a French LLM alongside the BU JD.'},
            {"label": 'Competitive international pathway', "sentiment": 'caution', "detail": 'Admission requires strong JD standing and Paris II LLM acceptance.'},
        ],
        "sources": [
            {"label": 'BU Law — program page', "url": 'https://www.bu.edu/academics/law/programs/jd-llm-in-international-commercial-and-investment-arbitration-at-paris2/'},
            {"label": 'U.S. News — BU School of Law', "url": 'https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-law-jdllm-in-european-law-at-paris-ii": {
        "summary": "BU Law's JD/LLM with Université Paris II (Panthéon-Assas) lets students earn a European-law LLM alongside the JD. Reviewers highlight the international credential, French civil-law training, and global legal-career preparation, while noting the program requires French-language coursework and extended study abroad.",
        "themes": [
            {"label": 'Paris civil-law LLM', "sentiment": 'positive', "detail": 'Students earn a European-law LLM from a leading French law faculty.'},
            {"label": 'Global legal career preparation', "sentiment": 'positive', "detail": 'Graduates pursue international law, diplomacy, and cross-border practice.'},
            {"label": 'Study-abroad commitment', "sentiment": 'caution', "detail": 'The pathway requires extended coursework in France beyond the Boston JD.'},
        ],
        "sources": [
            {"label": 'BU Law — program page', "url": 'https://www.bu.edu/academics/law/programs/jdllm-in-european-law-at-paris-ii/'},
            {"label": 'U.S. News — BU School of Law', "url": 'https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-law-jdllm-in-finance": {
        "summary": "BU Law's JD/LLM in Finance with Goethe University's Institute for Law and Finance sends third-year students to Frankfurt for a finance-law LLM. Reviewers praise the unique European finance-law credential, practitioner faculty from banks and regulators, and thesis-plus-internship structure, while noting students spend a full year abroad and must meet ILF admission standards.",
        "themes": [
            {"label": 'Frankfurt finance-law LLM', "sentiment": 'positive', "detail": 'Students train with ILF faculty drawn from banks, regulators, and global law firms.'},
            {"label": 'European financial-services focus', "sentiment": 'positive', "detail": 'Coursework covers transactional, regulatory, and economic aspects of global finance.'},
            {"label": 'Full-year abroad requirement', "sentiment": 'caution', "detail": 'Students spend the third JD year enrolled full-time at ILF in Frankfurt.'},
        ],
        "sources": [
            {"label": 'BU Law — program page', "url": 'https://www.bu.edu/academics/law/programs/jdllm-in-finance/'},
            {"label": 'U.S. News — BU School of Law', "url": 'https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-law-jdllm-in-international-and-european-business-law-at-icade": {
        "summary": "BU Law's JD/LLM with ICADE (Comillas Pontifical University, Madrid) combines American legal training with European business law. Reviewers cite the Spain-based LLM, cross-border corporate-law preparation, and BU Law's international dual-degree portfolio, while noting students must complete coursework in Madrid.",
        "themes": [
            {"label": 'European business-law LLM', "sentiment": 'positive', "detail": 'Students earn an ICADE LLM in international and European business law.'},
            {"label": 'Cross-border corporate practice', "sentiment": 'positive', "detail": 'Graduates pursue multinational corporate and trade-law roles.'},
            {"label": 'Madrid study requirement', "sentiment": 'caution', "detail": 'The LLM portion requires extended study at ICADE in Spain.'},
        ],
        "sources": [
            {"label": 'BU Law — program page', "url": 'https://www.bu.edu/academics/law/programs/jdllm-in-international-and-european-business-law-at-icade/'},
            {"label": 'U.S. News — BU School of Law', "url": 'https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-law-jdma-english": {
        "summary": "BU Law's JD/MA in English pairs legal training with graduate literary scholarship in CAS. Reviewers value the combined law-and-humanities credential for legal writing, academia, and public-interest roles, while noting the dual degree extends the JD timeline by roughly a year.",
        "themes": [
            {"label": 'Law and literary scholarship', "sentiment": 'positive', "detail": 'Students combine JD training with graduate English coursework and research.'},
            {"label": 'Legal writing and academia paths', "sentiment": 'positive', "detail": 'Graduates pursue legal scholarship, editing, and public-interest law.'},
            {"label": 'Extended JD timeline', "sentiment": 'caution', "detail": 'The MA adds a year of graduate English coursework beyond the three-year JD.'},
        ],
        "sources": [
            {"label": 'BU Law — program page', "url": 'https://www.bu.edu/academics/law/programs/jdma-english/'},
            {"label": 'U.S. News — BU School of Law', "url": 'https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-law-jdma-preservation": {
        "summary": "BU Law's JD/MA in Preservation Studies integrates legal training with historic-preservation scholarship through LAW and GRS. Reviewers praise the interdisciplinary land-use and heritage-law credential, Boston preservation internship sites, and compressed dual-degree timeline, while noting students must apply separately to GRS during the first year of law school.",
        "themes": [
            {"label": 'Law and preservation integration', "sentiment": 'positive', "detail": 'Students combine JD training with preservation theory, planning, and fieldwork.'},
            {"label": 'Historic preservation internships', "sentiment": 'positive', "detail": 'Summer placements include Historic New England and National Trust partners.'},
            {"label": 'Dual application process', "sentiment": 'caution', "detail": 'Students must gain separate GRS admission during the first year of law school.'},
        ],
        "sources": [
            {"label": 'BU Law — program page', "url": 'https://www.bu.edu/academics/law/programs/jdma-preservation/'},
            {"label": 'U.S. News — BU School of Law', "url": 'https://www.usnews.com/best-graduate-schools/top-law-schools/boston-university-01058'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sar-public-health-bs-mph": {
        "summary": "BU's BS-to-MPH program jointly offered by Sargent College and the School of Public Health lets undergraduates earn a Master of Public Health in five years. Reviewers praise the accelerated public-health credential, SPH's nationally ranked MPH, and Sargent health-sciences foundations, while noting admission requires a 3.2+ GPA and competitive SOPHAS application by sophomore or junior year.",
        "themes": [
            {"label": 'Five-year BS/MPH pathway', "sentiment": 'positive', "detail": 'Sargent undergraduates stack up to 12 SPH units toward the MPH.'},
            {"label": 'Top-ranked SPH training', "sentiment": 'positive', "detail": 'Students complete SPH core courses and a functional certificate.'},
            {"label": 'Competitive early admission', "sentiment": 'caution', "detail": 'Applicants need strong GPA and SOPHAS materials by sophomore or junior year.'},
        ],
        "sources": [
            {"label": 'BU SAR — BS-to-MPH', "url": 'https://www.bu.edu/academics/sar/programs/public-health/bs-mph/'},
            {"label": 'BU School of Public Health', "url": 'https://www.bu.edu/sph/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sdm-dental-public-health-dscd": {
        "summary": "BU's Doctor of Science in Dentistry in Dental Public Health (Goldman School of Dental Medicine) provides advanced specialty training for dentists within an accredited dental school. Reviewers cite SDM's specialty clinic resources, Boston hospital affiliations, and board-eligible training, while noting programs expect a DMD/DDS and competitive specialty admission.",
        "themes": [
            {"label": 'Dental Public Health specialty training', "sentiment": 'positive', "detail": 'Advanced clinical and research training in dental public health within SDM.'},
            {"label": 'Accredited dental-school setting', "sentiment": 'positive', "detail": "Training occurs within BU's accredited Goldman School of Dental Medicine."},
            {"label": 'Requires dental degree', "sentiment": 'caution', "detail": 'Admission expects a DMD/DDS and competitive specialty credentials.'},
        ],
        "sources": [
            {"label": 'BU SDM — Dental Public Health', "url": 'https://www.bu.edu/academics/sdm/programs/dental-public-health/'},
            {"label": 'BU Goldman School of Dental Medicine', "url": 'https://www.bu.edu/dental/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sdm-dental-public-health-msd": {
        "summary": "BU's Master of Science in Dentistry in Dental Public Health (Goldman School of Dental Medicine) provides advanced specialty training for dentists within an accredited dental school. Reviewers cite SDM's specialty clinic resources, Boston hospital affiliations, and board-eligible training, while noting programs expect a DMD/DDS and competitive specialty admission.",
        "themes": [
            {"label": 'Dental Public Health specialty training', "sentiment": 'positive', "detail": 'Advanced clinical and research training in dental public health within SDM.'},
            {"label": 'Accredited dental-school setting', "sentiment": 'positive', "detail": "Training occurs within BU's accredited Goldman School of Dental Medicine."},
            {"label": 'Requires dental degree', "sentiment": 'caution', "detail": 'Admission expects a DMD/DDS and competitive specialty credentials.'},
        ],
        "sources": [
            {"label": 'BU SDM — Dental Public Health', "url": 'https://www.bu.edu/academics/sdm/programs/dental-public-health/'},
            {"label": 'BU Goldman School of Dental Medicine', "url": 'https://www.bu.edu/dental/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sdm-operative-dentistry-dscd": {
        "summary": "BU's Doctor of Science in Dentistry in Operative Dentistry (Goldman School of Dental Medicine) provides advanced specialty training for dentists within an accredited dental school. Reviewers cite SDM's specialty clinic resources, Boston hospital affiliations, and board-eligible training, while noting programs expect a DMD/DDS and competitive specialty admission.",
        "themes": [
            {"label": 'Operative Dentistry specialty training', "sentiment": 'positive', "detail": 'Advanced clinical and research training in operative dentistry within SDM.'},
            {"label": 'Accredited dental-school setting', "sentiment": 'positive', "detail": "Training occurs within BU's accredited Goldman School of Dental Medicine."},
            {"label": 'Requires dental degree', "sentiment": 'caution', "detail": 'Admission expects a DMD/DDS and competitive specialty credentials.'},
        ],
        "sources": [
            {"label": 'BU SDM — Operative Dentistry', "url": 'https://www.bu.edu/academics/sdm/programs/operative-dentistry/'},
            {"label": 'BU Goldman School of Dental Medicine', "url": 'https://www.bu.edu/dental/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sdm-operative-dentistry-msd": {
        "summary": "BU's Master of Science in Dentistry in Operative Dentistry (Goldman School of Dental Medicine) provides advanced specialty training for dentists within an accredited dental school. Reviewers cite SDM's specialty clinic resources, Boston hospital affiliations, and board-eligible training, while noting programs expect a DMD/DDS and competitive specialty admission.",
        "themes": [
            {"label": 'Operative Dentistry specialty training', "sentiment": 'positive', "detail": 'Advanced clinical and research training in operative dentistry within SDM.'},
            {"label": 'Accredited dental-school setting', "sentiment": 'positive', "detail": "Training occurs within BU's accredited Goldman School of Dental Medicine."},
            {"label": 'Requires dental degree', "sentiment": 'caution', "detail": 'Admission expects a DMD/DDS and competitive specialty credentials.'},
        ],
        "sources": [
            {"label": 'BU SDM — Operative Dentistry', "url": 'https://www.bu.edu/academics/sdm/programs/operative-dentistry/'},
            {"label": 'BU Goldman School of Dental Medicine', "url": 'https://www.bu.edu/dental/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sdm-pediatric-dentistry-dscd": {
        "summary": "BU's Doctor of Science in Dentistry in Pediatric Dentistry (Goldman School of Dental Medicine) provides advanced specialty training for dentists within an accredited dental school. Reviewers cite SDM's specialty clinic resources, Boston hospital affiliations, and board-eligible training, while noting programs expect a DMD/DDS and competitive specialty admission.",
        "themes": [
            {"label": 'Pediatric Dentistry specialty training', "sentiment": 'positive', "detail": 'Advanced clinical and research training in pediatric dentistry within SDM.'},
            {"label": 'Accredited dental-school setting', "sentiment": 'positive', "detail": "Training occurs within BU's accredited Goldman School of Dental Medicine."},
            {"label": 'Requires dental degree', "sentiment": 'caution', "detail": 'Admission expects a DMD/DDS and competitive specialty credentials.'},
        ],
        "sources": [
            {"label": 'BU SDM — Pediatric Dentistry', "url": 'https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/'},
            {"label": 'BU Goldman School of Dental Medicine', "url": 'https://www.bu.edu/dental/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
    "bu-academics-sdm-pediatric-dentistry-msd": {
        "summary": "BU's Master of Science in Dentistry in Pediatric Dentistry (Goldman School of Dental Medicine) provides advanced specialty training for dentists within an accredited dental school. Reviewers cite SDM's specialty clinic resources, Boston hospital affiliations, and board-eligible training, while noting programs expect a DMD/DDS and competitive specialty admission.",
        "themes": [
            {"label": 'Pediatric Dentistry specialty training', "sentiment": 'positive', "detail": 'Advanced clinical and research training in pediatric dentistry within SDM.'},
            {"label": 'Accredited dental-school setting', "sentiment": 'positive', "detail": "Training occurs within BU's accredited Goldman School of Dental Medicine."},
            {"label": 'Requires dental degree', "sentiment": 'caution', "detail": 'Admission expects a DMD/DDS and competitive specialty credentials.'},
        ],
        "sources": [
            {"label": 'BU SDM — Pediatric Dentistry', "url": 'https://www.bu.edu/academics/sdm/programs/pediatric-dentistry/'},
            {"label": 'BU Goldman School of Dental Medicine', "url": 'https://www.bu.edu/dental/'},
        ],
        "disclaimer": 'Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, official department and employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or university endorsements.',
    },
}

# Migrate reviews from collapsed concentration-split slugs onto keeper programs.
for _old_slug, _new_slug in _SLUG_REDIRECT.items():
    if _old_slug in _REVIEWS_BY_SLUG:
        if _new_slug not in _REVIEWS_BY_SLUG:
            _REVIEWS_BY_SLUG[_new_slug] = _REVIEWS_BY_SLUG.pop(_old_slug)
        else:
            del _REVIEWS_BY_SLUG[_old_slug]


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = ["tracks"]
    tuition, _ = _program_tuition(spec)
    if tuition is None:
        omitted.append("cost_data.tuition_usd")
    if slug not in _OUTCOMES_BY_SLUG:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.median_salary",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
            "outcomes_data.source",
        ]
    else:
        omitted += _OUTCOMES_OMIT_BY_SLUG.get(slug, [])
    if slug not in _CLASS_PROFILE_BY_SLUG or _CLASS_PROFILE_BY_SLUG.get(slug, {}).get("cohort_size") is None:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    return _standard(omitted)


def apply(session: Session) -> bool:
    """Enrich Boston University to the canonical profile. Flushes; caller commits."""
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1839
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.bu.edu"
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
    existing = {s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))}
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


def _website_for(spec: dict) -> str:
    return _WEBSITE_OVERRIDE.get(spec["slug"], SCHOOL_WEBSITE[spec["school"]])


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
                institution_id=inst.id, program_name=spec["program_name"],
                degree_type=spec["degree_type"], slug=slug,
            )
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.delivery_format = spec.get("delivery_format", "on_campus")
        p.tracks = spec.get("tracks")
        p.application_requirements = _requirements_for(spec)
        p.tuition, p.cost_data = _program_tuition(spec)
        outcomes = dict(_OUTCOMES_BY_SLUG.get(slug, {}))
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
    for slug, p in existing.items():
        if slug not in canonical:
            if _program_has_dependents(session, p.id):
                p.is_published = False
            else:
                session.delete(p)
    session.flush()
