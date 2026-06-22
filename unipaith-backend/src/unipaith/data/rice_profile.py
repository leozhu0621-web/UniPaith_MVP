"""Rice University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``duke_profile.py``): every value is researched from an authoritative source and carries a
citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) — never
guessed. Built 2026-06-11 from:

  • U.S. Dept. of Education **College Scorecard** API + **NCES College Navigator** (IPEDS,
    UNITID 227757) — net price, earnings, completion/retention, Pell/loan, median debt.
  • Rice **Common Data Set 2024-25** (Office of Institutional Effectiveness) — enrollment,
    faculty, race/ethnicity, test scores, retention, six-year graduation rate.
  • Rice **Admission Class Profile** (Class of 2029) — applicants / admits / admit rate.
  • Rice **Center for Career Development** first-destination outcomes (Class of 2024).
  • Each school's official site + the Rice **General Announcements** catalog (ga.rice.edu)
    for deans, founding, research centers, and the full degree catalog; each program's
    official program page (degree, format, published tuition where Rice states one).
  • Rankings: **QS 2026**, **THE 2026**, **U.S. News 2026** (each cited), Carnegie (R1),
    SACSCOC accreditation.

Honest caveats stamped into ``_standard.omitted``: Rice publishes career outcomes
institution-wide (no per-program employment/industry split), so those program fields are
omitted; academic master's and PhD programs carry Rice's published 2025-26 standard
full-time graduate tuition ($62,474/yr; the matcher budget signal, with the funded
tuition-waiver+stipend reality noted separately), professional programs with a published
annual rate carry it, and only the per-credit professional / continuing-studies programs
(billed per credit with no single published annual figure) omit tuition with a sourced
per-credit record rather than a guessed number; notable-
faculty rosters are omitted for schools where no current named distinction could be
verified from an official page; and Rice's news site exposes no editorial RSS feed, so the
verified LiveWhale events RSS (current, image-carrying) feeds the Updates surface while the
iCalendar feeds Events (both verified HTTP 200 on 2026-06-11).

Depth pass (2026-06-15, riceprof4): merged ``DEPTH_REVIEWS`` for 51 coverable
programs — completes Rice coverable external_reviews (57/57).

Description repair (2026-06-17, riceprof5): replaces all name-prefixed
classification stubs with field-specific clauses from
``rice_field_descriptions.py`` (gold MIT/JHU pattern); 0% name-prefixed
descriptions.

Structural repair (2026-06-20, ricedefab1): undergraduate rows carry conferred
degree designations (not bare field names); ``department`` names Rice's real
owning unit (never ``program_name`` echoed verbatim); per-credential description
leads so credential siblings no longer share a verbatim body (REPAIR BACKLOG #4 —
gold MIT/JHU = 0% verbatim / shared-leading-body).

Per-credential bodies (2026-06-20, ricepercred1): the ``ricedefab1`` pass left a
single ``FIELD_DESCRIPTIONS`` clause stamped behind a swapped credential frame, so a
field's BA / MS / PhD rows still shared one body in the description TAIL — the run-65
credential-frame + tail-shared field body (REPAIR BACKLOG #3 / miss #8). This pass
gives every multi-credential field a distinct per-(field, degree_type) body from
``FIELD_CRED_DESCRIPTIONS`` (what THAT degree studies at THAT level) and drops the
redundant "Rice offers the … in {field}." classification lead; gold MIT = 0%
frame-stripped shared body, now enforced at import + in ``test_anti_stub_gate.py``.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.data.rice_field_descriptions import (
    FIELD_CRED_DESCRIPTIONS,
    FIELD_DESCRIPTIONS,
)
from unipaith.data.rice_reviews_depth import DEPTH_REVIEWS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze as _anti_stub_analyze
from unipaith.profile_standard.anti_stub import (
    frame_stripped_shared_body as _frame_stripped_shared_body,
)

INSTITUTION_NAME = "Rice University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-20"

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is an undergraduate .+ major in Rice University's .+\.$"
    r"|^.+ is (a research doctorate|a master's program|a professional master's program|"
    r"a graduate certificate) offered through Rice University's ",
)


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Every required institution-level field was verified from a citable source, so nothing is
# omitted at the institution level.
_OMITTED_INSTITUTION: list[str] = []

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects; each rank is quoted from the official ranking
# body for the 2026 edition. These already match the live Rice ranking_data (instenrich2);
# re-asserted here so the module is self-contained and idempotent.
RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "SACSCOC (Southern Association of Colleges and Schools Commission on Colleges)",
    # Carnegie 2025 basic classification (R1).
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    # QS World University Rankings 2026: Rice is #119 worldwide.
    "qs_world_university_rankings": {
        "rank": 119,
        "year": 2026,
        "source_url": "https://news.rice.edu/news/2025/rice-moves-more-20-spots-qs-world-university-rankings",
    },
    # THE World University Rankings 2026: #103 in the world.
    "times_higher_education": {
        "rank": 103,
        "year": 2026,
        "source_url": "https://news.rice.edu/news/2025/rice-climbs-9-spots-times-higher-education-global-rankings-places-among-worlds-top",
    },
    # U.S. News Best Colleges (National Universities) 2026: #17 nationally.
    "us_news_national": {
        "rank": 17,
        "year": 2026,
        "source_url": "https://news.rice.edu/news/2025/rice-rises-us-news-rankings-recognized-value-teaching-and-innovation",
    },
}

# school_outcomes is shallow-merged into the existing JSONB. The College Scorecard seed +
# instenrich2 already wrote admit_rate / avg_net_price / median_earnings_10yr / scale /
# research / campus_life / location; the sub-objects below fill the verified gaps the
# conformance check flagged (funnel, diversity, outcomes, cost & aid, retention/grad rate,
# feeds, citations) without clobbering the good existing values.
SCHOOL_OUTCOMES: dict = {
    # Rice Common Data Set 2024-25 (CDS-B22): first-year retention = 97.41% (Scorecard
    # pooled = 0.975). Six-year graduation rate (Fall 2018 cohort) = 94.6%.
    "retention_rate_first_year": 0.97,
    "graduation_rate_6yr": 0.946,
    # College Scorecard completion rate at 150% of normal time.
    "completion_rate_4yr_150pct": 0.9464,
    # Rice Admission Class Profile, Class of 2029: 2,948 admits / 36,791 applicants = 8.0%.
    "admit_rate": 0.080,
    # College Scorecard average annual net price (overall) + institution-wide median
    # earnings 10 years after entry (re-asserted from the live instenrich2 values, both cited
    # to the College Scorecard for UNITID 227757).
    "avg_net_price": 13370,
    "median_earnings_10yr": 89718,
    "financial_aid": {
        # NCES / College Scorecard (IPEDS): 17.0% of undergraduates received a Pell grant;
        # 6.5% took federal student loans (the Scorecard authoritative figure).
        "pell_grant_rate": 0.17,
        "federal_loan_rate": 0.065,
        # Rice Common Data Set 2025-26 (CDS-G) first-year billed direct cost:
        # tuition $66,540 + required fees $957 + food & housing $19,550 = $87,047.
        "cost_of_attendance": 87047,
        # College Scorecard median federal debt of completers.
        "median_debt_completers": 11000,
        # College Scorecard average annual net price (overall).
        "avg_net_price": 13370,
    },
    # Undergraduate race/ethnicity (Rice Common Data Set 2024-25, CDS-B2, degree-seeking
    # undergraduates, n = 4,776).
    "demographics": {
        "white": 0.256,
        "asian": 0.291,
        "hispanic": 0.167,
        "black": 0.079,
        "two_or_more": 0.055,
        "international": 0.128,
        "american_indian": 0.0015,
        "native_hawaiian": 0.0006,
        "unknown": 0.022,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (Rice CDS 2024-25, C9). Rice is
    # test-recommended (effectively test-optional) for the Fall 2026 cycle.
    "test_scores": {
        "sat_reading_25_75": [740, 770],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    # Rice Center for Career Development, Class of 2024 (97% knowledge rate): 86% employed or
    # continuing education within six months (53% working + 33% continuing education).
    "employed_or_continuing_ed": 0.86,
    # Rice CCD — bachelor's graduates' employment by industry, in rank order.
    "top_employer_industries": [
        "Technology",
        "Finance",
        "Consulting",
        "Healthcare & Biotech",
        "Energy",
        "Education",
        "Media",
        "Manufacturing",
    ],
    "campus_basics": {"location": "Houston, Texas"},
    # Scale, research, campus life, and geo-coordinates re-asserted from the live instenrich2
    # values (Rice Common Data Set / Rice Management Company / official institute pages); each
    # institute carries its official link so the campus-resources section renders with URLs.
    "scale": {
        "campus_acres": 300,
        "endowment_usd": 7900000000,
        "faculty_count": 896,
        "student_faculty_ratio": "6:1",
    },
    "location": {"lat": 29.7174, "lng": -95.4018},
    "research": {
        "labs": [
            "Smalley-Curl Institute",
            "Ken Kennedy Institute",
            "Baker Institute for Public Policy",
            "Kinder Institute for Urban Research",
            "Rice 360 Institute for Global Health",
            "Rice Space Institute",
            "Rice Advanced Materials Institute",
            "Rice Sustainability Institute",
        ],
        "areas": [
            "Nanoscale science and nanotechnology",
            "Quantum materials and quantum information science",
            "Computing, data science and information technology",
            "Public policy",
            "Bioengineering and global health",
            "Urban research and sustainability",
        ],
        "lab_links": {
            "Smalley-Curl Institute": "https://sci.rice.edu/",
            "Ken Kennedy Institute": "https://kenkennedy.rice.edu/",
            "Baker Institute for Public Policy": "https://www.bakerinstitute.org/",
            "Kinder Institute for Urban Research": "https://kinder.rice.edu/",
            "Rice 360 Institute for Global Health": "https://www.rice360.rice.edu/",
            "Rice Space Institute": "https://rsi.rice.edu/",
            "Rice Advanced Materials Institute": "https://rami.rice.edu/",
            "Rice Sustainability Institute": "https://si.rice.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (American Conference)",
        "varsity_sports": 14,
        "student_orgs": 300,
        "resources": [
            {"name": "Rice Student Center", "url": "https://studentcenter.rice.edu/"},
            {"name": "Rice Owls Athletics", "url": "https://riceowls.com/"},
            {"name": "Housing & Residential Colleges", "url": "https://housing.rice.edu/"},
            {"name": "Campus Life", "url": "https://www.rice.edu/campus-life"},
        ],
    },
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/"
                "Rice_University_-_Rice_statue_with_Lovett_Hall.JPG/"
                "1920px-Rice_University_-_Rice_statue_with_Lovett_Hall.JPG"
            ),
            "credit": "Wikimedia Commons / Daderot (public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/"
                "Rice_University_Main_Entrance.jpg/"
                "1920px-Rice_University_Main_Entrance.jpg"
            ),
            "credit": "Wikimedia Commons / Katie Haugland Bowen (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/"
                "Rice_University_Campus.jpg/1920px-Rice_University_Campus.jpg"
            ),
            "credit": "Wikimedia Commons / AnnaLellis (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/"
                "Rice_University_Sally_Port.jpg/1920px-Rice_University_Sally_Port.jpg"
            ),
            "credit": "Wikimedia Commons / Claudia Paine22 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/"
                "View_of_Rice_Stadium_with_Rice_University_campus_in_background.jpg/"
                "1920px-View_of_Rice_Stadium_with_Rice_University_campus_in_background.jpg"
            ),
            "credit": "Wikimedia Commons / Quintin Soloviev (CC BY 4.0)",
        },
    ],
    # Lovett Hall statue leads the hero; see ``campus_photos[0]``.
    "media_credit": "Wikimedia Commons / Daderot (public domain)",
    "flagship": {
        # Rice Common Data Set 2024-25 (CDS-B1): 4,789 undergraduate + 4,172 graduate = 8,961.
        "enrollment_total": 8961,
        # Rice Admission Class Profile — Class of 2029 (entering fall 2025).
        "applicants": 36791,
        "admits": 2948,
        "admissions_cycle": "Class of 2029 (entering fall 2025; Rice Admission Class Profile)",
        # Chartered 1891 by William Marsh Rice; opened to students September 23, 1912.
        "founded_year": 1912,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Rice, UNITID 227757)",
            "url": "https://collegescorecard.ed.gov/school/?227757-Rice-University",
        },
        {
            "label": "NCES College Navigator — Rice University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=227757",
        },
        {
            "label": "Rice University — Common Data Set 2024-25",
            "url": "https://ideas.rice.edu/wp-content/uploads/2025/10/CDS_2024-25_WEBSITE.pdf",
        },
        {
            "label": "Rice Admission — Class Profile (Class of 2029)",
            "url": "https://admission.rice.edu/apply/class-profile",
        },
        {
            "label": "Rice Center for Career Development — Career Outcomes",
            "url": "https://ccd.rice.edu/about/career-outcomes",
        },
        {
            "label": "Rice Management Company / Investments — Endowment",
            "url": "https://investments.rice.edu/",
        },
        {
            "label": "Carnegie Classifications — Rice University (R1)",
            "url": "https://carnegieclassifications.acenet.edu/institution/rice-university/",
        },
        {
            "label": "QS World University Rankings 2026 — Rice University (#119)",
            "url": "https://news.rice.edu/news/2025/rice-moves-more-20-spots-qs-world-university-rankings",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Rice (#103)",
            "url": "https://news.rice.edu/news/2025/rice-climbs-9-spots-times-higher-education-global-rankings-places-among-worlds-top",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Rice University (#17 National Universities)",
            "url": "https://www.usnews.com/best-colleges/rice-3604",
        },
        {
            "label": "Rice General Announcements — Accreditation",
            "url": "https://ga.rice.edu/important-notices/accreditation/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the
# total (8,961) lives in flagship.enrollment_total and renders as "Total enrollment".
UNDERGRAD_COUNT = 4789

DESCRIPTION = (
    "Rice University is a private research university in Houston, Texas. Chartered in 1891 "
    "by the Massachusetts-born cotton merchant William Marsh Rice and opened to students on "
    "September 23, 1912 as the William Marsh Rice Institute, it sits on a wooded 300-acre "
    "campus in the heart of Houston, next to the Texas Medical Center and the Museum "
    "District. It enrolls roughly 4,800 undergraduates and about 4,200 graduate and "
    "professional students — some 8,900 in all — under a residential-college system and a "
    "6:1 student-faculty ratio.\n\n"
    "Rice is organized into eight schools: the Wiess School of Natural Sciences, the George "
    "R. Brown School of Engineering and Computing, the School of Humanities and Arts, the "
    "School of Social Sciences, the Rice School of Architecture, the Shepherd School of "
    "Music, the Jesse H. Jones Graduate School of Business, and the Susanne M. Glasscock "
    "School of Continuing Studies. Undergraduates choose among more than fifty majors, and "
    "the graduate schools confer the master's, Ph.D., and professional degrees — including "
    "online and professional master's programs in business, computing, data science, and "
    "engineering.\n\n"
    "A Carnegie R1 university accredited by SACSCOC, Rice ranks among the strongest research "
    "universities in the country: No. 17 among national universities by U.S. News, No. 103 "
    "in the world by Times Higher Education, and No. 119 by QS. It admitted 8.0% of "
    "first-year applicants for the Class of 2029.\n\n"
    "Rice meets the full demonstrated financial need of admitted undergraduates through The "
    "Rice Investment, and its average net price is about $13,000 a year against a billed "
    "cost of attendance near $87,000; the median federal debt of completers is about "
    "$11,000. Among the Class of 2024, 86% of graduates were employed or continuing their "
    "education within six months, most heavily in technology, finance, and consulting. "
    "Rice's teams, the Owls, compete in NCAA Division I (the American Athletic Conference)."
)

# ── The real degree-granting schools (display order) ───────────────────────
_NS = "Wiess School of Natural Sciences"
_ENG = "George R. Brown School of Engineering and Computing"
_HUM = "School of Humanities and Arts"
_SOC = "School of Social Sciences"
_ARCH = "Rice School of Architecture"
_MUS = "The Shepherd School of Music"
_BIZ = "Jesse H. Jones Graduate School of Business"
_GLAS = "Susanne M. Glasscock School of Continuing Studies"

SCHOOLS: list[dict] = [
    {
        "name": _NS,
        "sort_order": 1,
        "description": (
            "The Wiess School of Natural Sciences advances fundamental understanding of the "
            "natural world while educating future discoverers. It comprises six departments — "
            "Chemistry; Physics & Astronomy; Mathematics; BioSciences; Earth, Environmental & "
            "Planetary Sciences; and Statistics-adjacent programs — and awards undergraduate "
            "majors, research Ph.D. and master's degrees, and a portfolio of industry-oriented "
            "professional science master's degrees."
        ),
    },
    {
        "name": _ENG,
        "sort_order": 2,
        "description": (
            "The George R. Brown School of Engineering and Computing — which added 'and "
            "Computing' to its name in 2024 — spans nine departments from bioengineering and "
            "computer science to materials science and statistics. It offers undergraduate "
            "degrees, thesis-based MS and Ph.D. programs, and a large slate of professional "
            "and online master's degrees in computing, data science, and engineering "
            "management."
        ),
    },
    {
        "name": _HUM,
        "sort_order": 3,
        "description": (
            "The School of Humanities and Arts — renamed in 2025 to recognize its growing "
            "investment in the visual arts, theatre, and creative writing — offers globally "
            "engaged programs across art history, English, history, philosophy, religion, and "
            "the languages, awarding the B.A., M.A., M.F.A., and Ph.D."
        ),
    },
    {
        "name": _SOC,
        "sort_order": 4,
        "description": (
            "The School of Social Sciences connects teaching and research with policy for the "
            "betterment of society. It comprises seven departments, serves more than a third "
            "of Rice undergraduates, and offers undergraduate majors, professional master's "
            "degrees, and Ph.D. programs in economics, political science, psychology, "
            "anthropology, and sociology."
        ),
    },
    {
        "name": _ARCH,
        "sort_order": 5,
        "description": (
            "The Rice School of Architecture is an international center of design research, "
            "experimentation, and debate. A small, selective school, it offers the "
            "professional Bachelor of Architecture and Master of Architecture degrees with an "
            "emphasis on global engagement and cross-disciplinary collaboration."
        ),
    },
    {
        "name": _MUS,
        "sort_order": 6,
        "description": (
            "The Shepherd School of Music cultivates the mastery of musical performance, "
            "combining a conservatory experience with the educational opportunities of a "
            "leading research university. It enrolls a selective community of about 275 "
            "musicians and awards the Bachelor of Music, Master of Music, Artist Diploma, and "
            "Doctor of Musical Arts."
        ),
    },
    {
        "name": _BIZ,
        "sort_order": 7,
        "description": (
            "The Jesse H. Jones Graduate School of Business — known publicly as Rice Business — "
            "offers a broad graduate portfolio: Full-Time, Professional, Hybrid, Executive, "
            "and Online MBA formats, a Master of Accounting, and a Ph.D. in Business. It now "
            "also houses the Virani Undergraduate School of Business."
        ),
    },
    {
        "name": _GLAS,
        "sort_order": 8,
        "description": (
            "The Susanne M. Glasscock School of Continuing Studies is Rice's continuing and "
            "professional education division, offering graduate degrees (the Master of Liberal "
            "Studies, Master of Interdisciplinary Studies, and Master of Arts in Teaching), "
            "professional development, educator certification, and lifelong-learning courses."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _NS: "https://naturalsciences.rice.edu/",
    _ENG: "https://engineering.rice.edu/",
    _HUM: "https://humanities.rice.edu/",
    _SOC: "https://socialsciences.rice.edu/",
    _ARCH: "https://arch.rice.edu/",
    _MUS: "https://music.rice.edu/",
    _BIZ: "https://business.rice.edu/",
    _GLAS: "https://glasscock.rice.edu/",
}

# Per-school about_detail (founded, leadership, notable faculty, research centers, named_for,
# source). Notable faculty are listed only where a current named distinction was verified
# from an official page; otherwise about_detail.faculty is omitted (recorded in
# _ABOUT_OMITTED), never guessed.
_ABOUT_DETAIL: dict[str, dict] = {
    _NS: {
        "founded": 1975,
        "leadership": "Thomas C. Killian — Dean of the Wiess School of Natural Sciences",
        "faculty": [
            "James M. Tour — T.T. and W.F. Chao Professor of Chemistry; elected to the "
            "National Academy of Engineering (2024)",
        ],
        "research_centers": [
            "Center for Theoretical Biological Physics",
            "Smalley-Curl Institute",
            "Rice Center for Quantum Materials",
            "Rice Space Institute",
            "Laboratory for Nanophotonics",
            "T. W. Bonner Nuclear Laboratory",
        ],
        "named_for": (
            "Harry and Olga Keith Wiess (renamed 1979); Harry C. Wiess co-founded Humble Oil, "
            "a predecessor of Exxon"
        ),
        "source": {
            "label": "Wiess School of Natural Sciences — About",
            "url": "https://naturalsciences.rice.edu/about",
        },
    },
    _ENG: {
        "founded": 1975,
        "leadership": (
            "Luay Nakhleh — William and Stephanie Sick Dean of the George R. Brown School of "
            "Engineering and Computing"
        ),
        "research_centers": [
            "Ken Kennedy Institute (K2I)",
            "Data to Knowledge Lab (D2K Lab)",
            "Richard Tapia Center for Excellence and Equity",
            "Smalley-Curl Institute",
            "Center for Theoretical Biological Physics",
            "SSPEED Center (Severe Storm Prediction, Education and Evacuation from Disasters)",
        ],
        "named_for": (
            "George Rufus Brown (1898–1983), Rice alumnus, co-founder of Brown & Root, and "
            "chairman of the Rice Board of Trustees"
        ),
        "source": {
            "label": "George R. Brown School of Engineering and Computing — About the Dean",
            "url": "https://engineering.rice.edu/about/leadership/about-dean",
        },
    },
    _HUM: {
        "founded": 1959,
        "leadership": (
            "Kathleen Canning — Andrew W. Mellon Professor of History and Dean of the School "
            "of Humanities and Arts"
        ),
        "faculty": [
            "W. Caleb McDaniel — Department of History; 2020 Pulitzer Prize for History "
            "('Sweet Taste of Liberty')",
            "Kathleen Canning — Andrew W. Mellon Professor of History (Dean)",
        ],
        "research_centers": [
            "Humanities Research Center",
            "Chao Center for Asian Studies",
            "Center for Latin American and Latinx Studies",
            "Center for the Study of Women, Gender and Sexuality",
            "Center for Environmental Studies",
            "Center for Languages and Intercultural Communication",
        ],
        "source": {
            "label": "School of Humanities and Arts — History",
            "url": "https://humanities.rice.edu/history-school-humanities-and-arts",
        },
    },
    _SOC: {
        "founded": 1979,
        "leadership": "Rachel Tolbert Kimbro — Dean of the School of Social Sciences",
        "faculty": [
            "Fred Oswald — Herbert S. Autrey Chair in Social Sciences; national associate of "
            "the National Academies of Sciences, Engineering and Medicine",
        ],
        "research_centers": [
            "Social Sciences Research Institute (SSRI)",
            "Center for African and African American Studies (CAAAS)",
            "Center for Coastal Futures and Adaptive Resilience",
            "Center for Computational Insights on Inequality and Society",
            "Institute of Health Resilience and Innovation",
            "Rice Center for Voting",
        ],
        "source": {
            "label": "School of Social Sciences — Dean Rachel Tolbert Kimbro",
            "url": "https://socialsciences.rice.edu/dean-rachel-tolbert-kimbro",
        },
    },
    _ARCH: {
        "leadership": "Igor Marjanović — William Ward Watkin Dean of the Rice School of Architecture",
        "faculty": [
            "Albert Pope — Gus Sessions Wortham Professor of Architecture",
            "Mónica Rivera — Harry K. and Albert K. Smith Professor of Architecture",
        ],
        "research_centers": [
            "Rice Design Alliance",
            "Rice Building Workshop",
            "Construct (design-build program)",
            "Rice Architecture Paris (global program)",
        ],
        "source": {
            "label": "Rice School of Architecture — Dean",
            "url": "https://arch.rice.edu/school/dean",
        },
    },
    _MUS: {
        "founded": 1975,
        "leadership": "Matthew Loden — Lynette S. Autrey Dean of Music",
        "research_centers": [
            "Brockman Hall for Opera",
            "Alice Pratt Brown Hall",
            "Stude Concert Hall",
            "Duncan Recital Hall",
            "Edythe Bates Old Recital Hall",
        ],
        "named_for": "Sallie Shepherd Perkins, who endowed the school",
        "source": {
            "label": "The Shepherd School of Music — History",
            "url": "https://music.rice.edu/about/history-shepherd-school",
        },
    },
    _BIZ: {
        "founded": 1974,
        "leadership": (
            "Jeff Fleming — Interim Dean and Fayez Sarofim Vanguard Professor of Finance"
        ),
        "faculty": [
            "Kerry Back — J. Howard Creekmore Professor of Finance; Financial Management "
            "Association Innovation in Teaching Award",
        ],
        "research_centers": [
            "Liu Idea Lab for Innovation and Entrepreneurship (Lilie)",
            "Rice Alliance for Technology and Entrepreneurship",
            "Center for Customer-Based Execution and Strategy (C-CUBES)",
            "Rice Business Finance Center",
        ],
        "named_for": (
            "Jesse H. Jones, the Houston business and civic leader; the school was established "
            "in 1974 with a gift from Houston Endowment Inc."
        ),
        "source": {
            "label": "Jesse H. Jones Graduate School of Business — About",
            "url": "https://business.rice.edu/about",
        },
    },
    _GLAS: {
        "founded": 1967,
        "leadership": "Robert Bruce Jr. — Dean of the Glasscock School of Continuing Studies",
        "research_centers": [
            "Rice Center for Education",
            "Center for Philanthropy and Nonprofit Leadership",
            "Center for Community Learning and Engagement",
            "English as a Second Language and Foreign Languages programs",
        ],
        "named_for": (
            "Susanne M. Glasscock; the school was renamed in 2006 following an endowment gift "
            "from the Glasscock Foundation"
        ),
        "source": {
            "label": "Glasscock School of Continuing Studies — About",
            "url": "https://glasscock.rice.edu/continuing-studies",
        },
    },
}

# Per-school honestly-omitted about_detail fields (verified-unavailable), for _standard.
_ABOUT_OMITTED: dict[str, list[str]] = {
    # No current named-prize holder verified from an official engineering page (the school
    # reports ~16 NAE members among faculty but does not name them).
    _ENG: ["about_detail.faculty"],
    # Not a named school (descriptive discipline name).
    _HUM: ["about_detail.named_for"],
    _SOC: ["about_detail.named_for"],
    # Rice's School of Architecture is not given a founding year on its official pages
    # (architecture has been taught since Rice's 1912 opening, corroborated but not
    # first-party), and the school carries no honorific name.
    _ARCH: ["about_detail.founded", "about_detail.named_for"],
    # The current-faculty page lists musicians by instrument without named chairs or awards.
    _MUS: ["about_detail.faculty"],
    # A continuing/professional-education school staffed by Rice faculty and practitioners;
    # no current named-prize holder is verified on an official page.
    _GLAS: ["about_detail.faculty"],
}

# ── Feeds (content_sources) ────────────────────────────────────────────────
# The daily content-ingest reads news_rss (RSS), events_feed (iCalendar), keywords (a
# word-boundary relevance filter) and news_curated (keep every item). Rice's news site
# (news.rice.edu, Drupal) exposes NO editorial RSS feed (all feed paths 404, verified
# 2026-06-11), so the verified LiveWhale events RSS — current and image-carrying — feeds the
# Updates surface, while the LiveWhale iCalendar feeds Events. Both verified HTTP 200.
_RICE_EVENTS_RSS = "https://events.rice.edu/live/rss/events"
_RICE_EVENTS_ICS = {"url": "https://events.rice.edu/live/ical/events", "type": "ical"}
_RICE_NEWS_URL = "https://news.rice.edu"

# Official university social handles (rice.edu site footer, verified 2026-06-11).
_SOCIAL_RICE = {
    "instagram": "https://www.instagram.com/riceuniversity/",
    "linkedin": "https://www.linkedin.com/school/riceuniversity/",
    "x": "https://twitter.com/riceuniversity",
    "youtube": "https://www.youtube.com/riceuniversity",
    "facebook": "https://www.facebook.com/RiceUniversity/",
}

# Per-school official handles, verified per channel 2026-06-11 (school sites + social pages).
# Only handles confirmed to exist are listed; a school that does not run a given channel
# simply omits that key (never guessed).
_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _NS: {
        "instagram": "https://www.instagram.com/RiceNatSci/",
        "x": "https://twitter.com/RiceNatSci",
        "facebook": "https://www.facebook.com/RiceNatSci",
    },
    _ENG: {
        "instagram": "https://www.instagram.com/riceengineering/",
        "linkedin": "https://www.linkedin.com/school/riceengineering/",
        "x": "https://twitter.com/riceengineering",
        "youtube": "https://www.youtube.com/riceengineering",
        "facebook": "https://www.facebook.com/riceengineering",
    },
    _HUM: {
        "instagram": "https://www.instagram.com/ricehumanities/",
        "linkedin": "https://www.linkedin.com/school/rice-humanities-and-arts/",
        "x": "https://x.com/RiceHumanities",
        "youtube": "https://www.youtube.com/ricehumanities",
        "facebook": "https://www.facebook.com/RiceHumanities/",
    },
    _SOC: {
        "instagram": "https://www.instagram.com/ricesocsci/",
        "linkedin": "https://www.linkedin.com/school/rice-university-school-of-social-sciences",
        "x": "https://twitter.com/RiceSocSci",
        "facebook": "https://www.facebook.com/RiceSocSci/",
    },
    _ARCH: {
        "instagram": "https://www.instagram.com/ricearch/",
        "linkedin": "https://www.linkedin.com/company/rice-school-of-architecture/",
        "facebook": "https://www.facebook.com/RiceArch/",
    },
    _MUS: {
        "instagram": "https://www.instagram.com/shepherd_school/",
        "facebook": "https://www.facebook.com/ShepherdSchool/",
    },
    _BIZ: {
        "instagram": "https://www.instagram.com/rice_business/",
        "linkedin": "https://www.linkedin.com/school/rice-business/",
        "x": "https://x.com/Rice_Biz",
        "youtube": "https://www.youtube.com/c/ricebusiness",
        "facebook": "https://www.facebook.com/BusinessRice",
    },
    _GLAS: {
        "instagram": "https://www.instagram.com/ricecontinuingstudies/",
        "linkedin": "https://www.linkedin.com/company/ricecontinuingstudies",
        "x": "https://twitter.com/glasscockschool",
        "youtube": "https://www.youtube.com/user/ricecontstudies",
        "facebook": "https://www.facebook.com/ricecontinuingstudies/",
    },
}

# Per-school feed config: the shared Rice events RSS + iCalendar, a school news page, and
# keywords that identify the school's items in the shared feed (the MIT/MBAn pattern). Rice
# has no per-school RSS, so the shared feed is keyword-filtered per school.
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _NS: {
        "news_url": "https://news.rice.edu/tag/natural-sciences",
        "keywords": ["natural sciences", "Wiess School", "Rice Natural Sciences"],
    },
    _ENG: {
        "news_url": "https://engineering.rice.edu/news-events",
        "keywords": ["Rice engineering", "computing", "George R. Brown"],
    },
    _HUM: {
        "news_url": "https://humanities.rice.edu/news",
        "keywords": ["humanities", "arts", "Sarofim Hall"],
    },
    _SOC: {
        "news_url": "https://news.rice.edu/tag/social-sciences",
        "keywords": ["social sciences", "Kraft Hall"],
    },
    _ARCH: {
        "news_url": "https://arch.rice.edu/school/news",
        "keywords": ["Rice Architecture", "School of Architecture", "Rice Building Workshop"],
    },
    _MUS: {
        "news_url": "https://music.rice.edu/news",
        "keywords": ["Shepherd School", "music", "Brockman Hall"],
    },
    _BIZ: {
        "news_url": "https://business.rice.edu/news",
        "keywords": ["Rice Business", "Jones Graduate School", "MBA"],
    },
    _GLAS: {
        "news_url": "https://glasscock.rice.edu/blog",
        "keywords": ["Glasscock School", "continuing studies", "lifelong learning"],
    },
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from the shared Rice feeds + keywords + socials."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": _RICE_EVENTS_RSS,
        "news_url": spec["news_url"],
        "news_curated": False,
        "events_feed": dict(_RICE_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_RICE),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide feed: the verified Rice events RSS (every item is official Rice content)
# + the Rice events iCalendar, with the official university social handles.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _RICE_EVENTS_RSS,
    "news_url": _RICE_NEWS_URL,
    "news_curated": True,
    "events_feed": dict(_RICE_EVENTS_ICS),
    "social": _SOCIAL_RICE,
}

# ── The program catalog (real majors/degrees, organized by school) ─────────
# Undergraduate majors per school (Rice General Announcements — Departments & Programs;
# cross-checked against the College Scorecard Fields of Study for UNITID 227757). Each tuple
# is (major name, degree codes) and produces one residential bachelor's program.
_UG_BY_SCHOOL: dict[str, list[tuple[str, str]]] = {
    _NS: [
        ("Astronomy", "BA"),
        ("Astrophysics", "BS"),
        ("Biosciences", "BA/BS"),
        ("Chemical Physics", "BS"),
        ("Chemistry", "BA/BS"),
        ("Earth, Environmental and Planetary Sciences", "BA/BS"),
        ("Environmental Science", "BA/BS"),
        ("Health Sciences", "BA"),
        ("Mathematics", "BA/BS"),
        ("Neuroscience", "BA/BS"),
        ("Physics", "BA/BS"),
        ("Sports Medicine and Exercise Physiology", "BA"),
    ],
    _ENG: [
        ("Artificial Intelligence", "BS"),
        ("Bioengineering", "BS"),
        ("Chemical and Biomolecular Engineering", "BS"),
        ("Chemical Engineering", "BA"),
        ("Civil Engineering", "BS"),
        ("Civil and Environmental Engineering", "BA"),
        ("Computational and Applied Mathematics", "BA"),
        ("Computer Science", "BA/BS"),
        ("Electrical and Computer Engineering", "BA/BS"),
        ("Environmental Engineering", "BS"),
        ("Materials Science and NanoEngineering", "BA/BS"),
        ("Mechanical Engineering", "BA/BS"),
        ("Operations Research", "BS"),
        ("Statistics", "BA/BS"),
    ],
    _HUM: [
        ("Ancient Mediterranean Civilizations", "BA"),
        ("Art (Studio Art)", "BA"),
        ("Art History", "BA"),
        ("Asian Studies", "BA"),
        ("Classical Studies", "BA"),
        ("English", "BA"),
        ("European Studies", "BA"),
        ("French Studies", "BA"),
        ("German Studies", "BA"),
        ("History", "BA"),
        ("Latin American and Latinx Studies", "BA"),
        ("Media Studies", "BA"),
        ("Philosophy", "BA"),
        ("Religion", "BA"),
        ("Spanish and Portuguese", "BA"),
        ("Study of Women, Gender and Sexuality", "BA"),
    ],
    _SOC: [
        ("Anthropology", "BA"),
        ("Cognitive Sciences", "BA"),
        ("Economics", "BA"),
        ("Global Affairs", "BA"),
        ("Linguistics", "BA"),
        ("Managerial Economics and Organizational Sciences", "BA"),
        ("Mathematical Economic Analysis", "BA"),
        ("Psychology", "BA"),
        ("Social Policy Analysis", "BA"),
        ("Sociology", "BA"),
        ("Sport Analytics", "BA"),
        ("Sport Management", "BA"),
    ],
    _ARCH: [
        ("Architecture", "BA/BArch"),
        ("Architectural Studies", "BA"),
    ],
    _MUS: [
        ("Music", "BA/BMus"),
        ("Music Composition", "BMus"),
        ("Music History", "BMus"),
        ("Music Theory", "BMus"),
    ],
    _BIZ: [
        ("Business", "BA"),
    ],
}

# Graduate / professional programs (degree-granting), each verified from its school's
# official program page or the Rice General Announcements catalog. Tuple:
#   (name, degree_type, school, department, duration_months, delivery_format, website,
#    tuition_usd | None, tuition_kind)
#   degree_type ∈ {masters, professional, phd, certificate}
#   tuition_kind ∈ {"year", "total", None}; None tuition → cost recorded "see program page".
_GA = "https://ga.rice.edu/programs-study/departments-programs"
_GRAD_EXPLICIT: list[tuple] = [
    # ── Jesse H. Jones Graduate School of Business ──
    ("Master of Business Administration (Full-Time MBA)", "masters", _BIZ, "Rice Business", 22, "on_campus", "https://business.rice.edu/rice-mba/full-time-mba", None, None),
    ("Professional MBA — Evening", "professional", _BIZ, "Rice Business", 22, "on_campus", "https://business.rice.edu/rice-mba/professional-mba", None, None),
    ("Professional MBA — Weekend", "professional", _BIZ, "Rice Business", 22, "on_campus", "https://business.rice.edu/rice-mba/professional-mba", None, None),
    ("Hybrid MBA", "professional", _BIZ, "Rice Business", 22, "hybrid", "https://business.rice.edu/rice-mba/hybrid-mba", 137700, "total"),
    ("Executive MBA", "professional", _BIZ, "Rice Business", 22, "on_campus", "https://business.rice.edu/rice-mba/executive-mba", 76125, "year"),
    ("MBA@Rice (Online MBA)", "professional", _BIZ, "Rice Business", 24, "online", "https://business.rice.edu/rice-mba/online-mba", None, None),
    ("Master of Accounting (MAcc)", "masters", _BIZ, "Rice Business", 10, "on_campus", "https://business.rice.edu/graduate-programs/master-accounting", 62596, "year"),
    ("Doctor of Philosophy in Business", "phd", _BIZ, "Rice Business", 60, "on_campus", "https://business.rice.edu/graduate-programs/phd-business", None, None),
    ("Graduate Certificate in Healthcare Management", "certificate", _BIZ, "Rice Business", 10, "on_campus", "https://business.rice.edu/graduate-programs/healthcare/healthcare-certificate", 25000, "total"),
    # ── George R. Brown School of Engineering and Computing ──
    ("Doctor of Philosophy in Bioengineering", "phd", _ENG, "Bioengineering", 60, "on_campus", "https://bioengineering.rice.edu/academics/phd-program", None, None),
    ("Master of Bioengineering (MBE) — Applied Bioengineering", "professional", _ENG, "Bioengineering", 24, "on_campus", "https://bioengineering.rice.edu/academics/masters-programs", None, None),
    ("Master of Bioengineering (MBE) — Global Medical Innovation", "professional", _ENG, "Bioengineering", 12, "on_campus", "https://bioengineering.rice.edu/academics/masters-programs", None, None),
    ("Doctor of Philosophy in Chemical and Biomolecular Engineering", "phd", _ENG, "Chemical and Biomolecular Engineering", 60, "on_campus", "https://chbe.rice.edu/academics/graduate-programs/phd-program", None, None),
    ("Master of Chemical Engineering (MChE)", "professional", _ENG, "Chemical and Biomolecular Engineering", 18, "on_campus", "https://chbe.rice.edu/academics/graduate-programs/mche-program", None, None),
    ("Doctor of Philosophy in Civil and Environmental Engineering", "phd", _ENG, "Civil and Environmental Engineering", 60, "on_campus", "https://cee.rice.edu/academics/graduate-programs/phd-program", None, None),
    ("Master of Science in Civil and Environmental Engineering", "masters", _ENG, "Civil and Environmental Engineering", 24, "on_campus", "https://cee.rice.edu/prospective-current-students/graduate-programs/master-science-program", None, None),
    ("Master of Civil and Environmental Engineering (MCEE)", "professional", _ENG, "Civil and Environmental Engineering", 18, "on_campus", "https://cee.rice.edu/academics/graduate-programs/master-civil-and-environmental-engineering", None, None),
    ("Doctor of Philosophy in Computer Science", "phd", _ENG, "Computer Science", 60, "on_campus", "https://cs.rice.edu/academics/graduate-programs/phd-program", None, None),
    ("Master of Science in Computer Science", "masters", _ENG, "Computer Science", 24, "on_campus", f"{_GA}/engineering/computer-science/", None, None),
    ("Master of Computer Science (MCS)", "professional", _ENG, "Computer Science", 18, "on_campus", "https://cs.rice.edu/academics/graduate-programs/professional-masters", None, None),
    ("Master of Computer Science (MCS@Rice, Online)", "professional", _ENG, "Computer Science", 18, "online", "https://cs.rice.edu/academics/graduate-programs/online-mcs", 51000, "total"),
    ("Doctor of Philosophy in Computational Applied Mathematics and Operations Research", "phd", _ENG, "Computational Applied Mathematics and Operations Research", 60, "on_campus", "https://cmor.rice.edu/academics/graduate-programs/phd-program", None, None),
    ("Master of Computational and Applied Mathematics (MCAAM)", "professional", _ENG, "Computational Applied Mathematics and Operations Research", 18, "on_campus", "https://cmor.rice.edu/academics/graduate-programs/professional-masters-programs", None, None),
    ("Master of Industrial Engineering (MIE)", "professional", _ENG, "Computational Applied Mathematics and Operations Research", 18, "on_campus", "https://epmp.rice.edu/programs/master-industrial-engineering", None, None),
    ("Master of Data Science (MDS)", "professional", _ENG, "Computer Science", 18, "on_campus", "https://csweb.rice.edu/academics/graduate-programs/professional-master-data-science", None, None),
    ("Master of Data Science (MDS@Rice, Online)", "professional", _ENG, "Computer Science", 24, "online", "https://cs.rice.edu/academics/graduate-programs/online-mds", 52700, "total"),
    ("Doctor of Philosophy in Electrical and Computer Engineering", "phd", _ENG, "Electrical and Computer Engineering", 60, "on_campus", "https://ece.rice.edu/academics/graduate-programs/phd-program", None, None),
    ("Master of Science in Electrical and Computer Engineering", "masters", _ENG, "Electrical and Computer Engineering", 24, "on_campus", "https://ece.rice.edu/academics/graduate-programs", None, None),
    ("Master of Electrical and Computer Engineering (MECE)", "professional", _ENG, "Electrical and Computer Engineering", 18, "on_campus", "https://ece.rice.edu/academics/graduate-programs/mee-program", None, None),
    ("Doctor of Philosophy in Materials Science and NanoEngineering", "phd", _ENG, "Materials Science and NanoEngineering", 60, "on_campus", "https://msne.rice.edu/academics/graduate-programs/phd-program", None, None),
    ("Master of Materials Science and NanoEngineering (MMSNE)", "professional", _ENG, "Materials Science and NanoEngineering", 18, "on_campus", "https://msne.rice.edu/academics/graduate-programs/mmsne-program", None, None),
    ("Doctor of Philosophy in Mechanical Engineering", "phd", _ENG, "Mechanical Engineering", 60, "on_campus", "https://mech.rice.edu/academics/graduate-programs/professional-masters-program", None, None),
    ("Master of Science in Mechanical Engineering", "masters", _ENG, "Mechanical Engineering", 24, "on_campus", f"{_GA}/engineering/mechanical-engineering/", None, None),
    ("Master of Mechanical Engineering (MME)", "professional", _ENG, "Mechanical Engineering", 18, "on_campus", "https://mech.rice.edu/academics/graduate-programs/professional-masters-program", None, None),
    ("Doctor of Philosophy in Statistics", "phd", _ENG, "Statistics", 60, "on_campus", "https://statistics.rice.edu/academics/graduate/phd", None, None),
    ("Master of Arts in Statistics", "masters", _ENG, "Statistics", 24, "on_campus", f"{_GA}/engineering/statistics/", None, None),
    ("Master of Statistics (MStat)", "professional", _ENG, "Statistics", 18, "on_campus", "https://statistics.rice.edu/academics/graduate/master-statistics", None, None),
    ("Master of Computational Science and Engineering (MCSE)", "professional", _ENG, "Engineering and Computing", 18, "on_campus", f"{_GA}/engineering/computational-science-engineering/computational-science-engineering-mcse/", None, None),
    ("Master of Energy Transition and Sustainability (METS)", "professional", _ENG, "Engineering and Natural Sciences", 18, "on_campus", "https://mets.rice.edu", 59100, "total"),
    ("Master of Engineering Management and Leadership (MEML)", "professional", _ENG, "Engineering and Computing", 18, "on_campus", "https://engineering.rice.edu/academics/graduate-programs/master-engineering-management-and-leadership/oncampus", None, None),
    ("Master of Engineering Management and Leadership (MEML, Online)", "professional", _ENG, "Engineering and Computing", 18, "online", "https://engineering.rice.edu/academics/graduate-programs/online-meml", None, None),
    ("Master of Digital Health (MDH)", "professional", _ENG, "Engineering and Computing", 18, "on_campus", f"{_GA}/engineering/digital-health/", None, None),
    # ── Wiess School of Natural Sciences ──
    ("Doctor of Philosophy in Biochemistry and Cell Biology", "phd", _NS, "BioSciences", 60, "on_campus", f"{_GA}/natural-sciences/biosciences/", None, None),
    ("Doctor of Philosophy in Ecology and Evolutionary Biology", "phd", _NS, "BioSciences", 60, "on_campus", f"{_GA}/natural-sciences/biosciences/", None, None),
    ("Master of Science in Biochemistry and Cell Biology", "masters", _NS, "BioSciences", 24, "on_campus", f"{_GA}/natural-sciences/biosciences/", None, None),
    ("Master of Science in Ecology and Evolutionary Biology", "masters", _NS, "BioSciences", 24, "on_campus", f"{_GA}/natural-sciences/biosciences/", None, None),
    ("Doctor of Philosophy in Chemistry", "phd", _NS, "Chemistry", 60, "on_campus", f"{_GA}/natural-sciences/chemistry/", None, None),
    ("Master of Arts in Chemistry", "masters", _NS, "Chemistry", 24, "on_campus", f"{_GA}/natural-sciences/chemistry/", None, None),
    ("Doctor of Philosophy in Earth, Environmental and Planetary Sciences", "phd", _NS, "Earth, Environmental and Planetary Sciences", 60, "on_campus", f"{_GA}/natural-sciences/earth-environmental-planetary-sciences/", None, None),
    ("Master of Science in Earth, Environmental and Planetary Sciences", "masters", _NS, "Earth, Environmental and Planetary Sciences", 24, "on_campus", f"{_GA}/natural-sciences/earth-environmental-planetary-sciences/", None, None),
    ("Doctor of Philosophy in Physics", "phd", _NS, "Physics and Astronomy", 60, "on_campus", f"{_GA}/natural-sciences/physics-astronomy/", None, None),
    ("Master of Science in Physics", "masters", _NS, "Physics and Astronomy", 24, "on_campus", "https://physics.rice.edu/ms-degree", None, None),
    ("Doctor of Philosophy in Applied Physics", "phd", _NS, "Applied Physics", 60, "on_campus", f"{_GA}/interdisciplinary/applied-physics/applied-physics-phd/", None, None),
    ("Doctor of Philosophy in Mathematics", "phd", _NS, "Mathematics", 60, "on_campus", f"{_GA}/natural-sciences/mathematics/", None, None),
    ("Master of Arts in Mathematics", "masters", _NS, "Mathematics", 24, "on_campus", f"{_GA}/natural-sciences/mathematics/", None, None),
    ("Doctor of Philosophy in Systems, Synthetic, and Physical Biology", "phd", _NS, "Systems, Synthetic and Physical Biology", 60, "on_campus", f"{_GA}/engineering/systems-synthetic-physical-biology/", None, None),
    ("Master of Science Teaching (MST)", "professional", _NS, "Science Teaching", 24, "on_campus", f"{_GA}/natural-sciences/science-teaching/teaching-mst/", None, None),
    ("Master of Science in Applied Chemical Sciences (MSACS)", "professional", _NS, "Professional Science Master's", 18, "on_campus", "https://profms.rice.edu/programs/applied-chemical-sciences", 59850, "total"),
    ("Master of Science in Bioscience and Health Policy (MSBHP)", "professional", _NS, "Professional Science Master's", 18, "on_campus", "https://profms.rice.edu/programs/bioscience-and-health-policy", 59850, "total"),
    ("Master of Science in Energy Geoscience (MSEG)", "professional", _NS, "Professional Science Master's", 18, "on_campus", "https://profms.rice.edu/programs/energy-geoscience", 59850, "total"),
    ("Master of Science in Environmental Analysis (MSEA)", "professional", _NS, "Professional Science Master's", 18, "on_campus", "https://profms.rice.edu/programs/environmental-analysis", 59850, "total"),
    ("Master of Science in Space Studies (MSSpS)", "professional", _NS, "Professional Science Master's", 18, "on_campus", "https://profms.rice.edu/programs/space-studies", 59850, "total"),
    # ── School of Humanities and Arts ──
    ("Master of Arts in Art History", "masters", _HUM, "Art History", 24, "on_campus", "https://arthistory.rice.edu/graduate-about", None, None),
    ("Doctor of Philosophy in Art History", "phd", _HUM, "Art History", 60, "on_campus", "https://arthistory.rice.edu/graduate-about", None, None),
    ("Master of Arts in English", "masters", _HUM, "English", 24, "on_campus", "https://english.rice.edu/what-we-do", None, None),
    ("Doctor of Philosophy in English", "phd", _HUM, "English", 60, "on_campus", f"{_GA}/humanities/english/english-phd/", None, None),
    ("Master of Fine Arts in Creative Writing", "masters", _HUM, "English", 24, "on_campus", "https://english.rice.edu/what-we-do", None, None),
    ("Master of Arts in History", "masters", _HUM, "History", 24, "on_campus", "https://history.rice.edu/graduate-program-overview", None, None),
    ("Doctor of Philosophy in History", "phd", _HUM, "History", 60, "on_campus", "https://history.rice.edu/graduate-program-overview", None, None),
    ("Master of Arts in Philosophy", "masters", _HUM, "Philosophy", 24, "on_campus", "https://philosophy.rice.edu/phd-philosophy", None, None),
    ("Doctor of Philosophy in Philosophy", "phd", _HUM, "Philosophy", 60, "on_campus", "https://philosophy.rice.edu/phd-philosophy", None, None),
    ("Master of Arts in Religion", "masters", _HUM, "Religion", 24, "on_campus", "https://reli.rice.edu/graduate-studies-religion", None, None),
    ("Doctor of Philosophy in Religion", "phd", _HUM, "Religion", 60, "on_campus", "https://reli.rice.edu/graduate-studies-religion", None, None),
    # ── School of Social Sciences ──
    ("Master of Arts in Anthropology", "masters", _SOC, "Anthropology", 24, "on_campus", "https://anthropology.rice.edu/graduate-studies", None, None),
    ("Doctor of Philosophy in Anthropology", "phd", _SOC, "Anthropology", 60, "on_campus", "https://anthropology.rice.edu/graduate-studies", None, None),
    ("Master of Arts in Economics", "masters", _SOC, "Economics", 24, "on_campus", "https://economics.rice.edu/graduate-program", None, None),
    ("Doctor of Philosophy in Economics", "phd", _SOC, "Economics", 60, "on_campus", "https://economics.rice.edu/graduate-program", None, None),
    ("Master of Arts in Political Science", "masters", _SOC, "Political Science", 24, "on_campus", "https://politicalscience.rice.edu/graduate-studies", None, None),
    ("Doctor of Philosophy in Political Science", "phd", _SOC, "Political Science", 60, "on_campus", "https://politicalscience.rice.edu/graduate-studies", None, None),
    ("Master of Arts in Psychology", "masters", _SOC, "Psychological Sciences", 24, "on_campus", "https://psychology.rice.edu/graduate", None, None),
    ("Doctor of Philosophy in Psychology", "phd", _SOC, "Psychological Sciences", 60, "on_campus", "https://psychology.rice.edu/graduate", None, None),
    ("Master of Arts in Sociology", "masters", _SOC, "Sociology", 24, "on_campus", "https://sociology.rice.edu/graduate", None, None),
    ("Doctor of Philosophy in Sociology", "phd", _SOC, "Sociology", 60, "on_campus", f"{_GA}/social-sciences/sociology/sociology-phd/", None, None),
    ("Master of Computational Economics (MCEcon)", "professional", _SOC, "Economics", 24, "on_campus", "https://economics.rice.edu/graduate-program/mcecon", None, None),
    ("Master of Energy Economics (MEEcon)", "professional", _SOC, "Economics", 24, "on_campus", "https://economics.rice.edu/graduate-program/MEECON", None, None),
    ("Master of Global Affairs (MGA)", "professional", _SOC, "Global Affairs", 24, "on_campus", "https://mga.rice.edu", 58000, "year"),
    ("Master of Human-Computer Interaction and Human Factors (MHCIHF)", "professional", _SOC, "Psychological Sciences", 24, "on_campus", "https://psychology.rice.edu/MHCIHF", 35000, "year"),
    ("Master of Industrial-Organizational Psychology (MIOP)", "professional", _SOC, "Psychological Sciences", 24, "on_campus", "https://psychology.rice.edu/miop", 35000, "year"),
    ("Master of Social Policy Evaluation (MSPE)", "professional", _SOC, "Social Policy Analysis", 12, "on_campus", "https://socialpolicy.rice.edu/", 44000, "year"),
    # ── Rice School of Architecture ──
    ("Master of Architecture (MArch) — Option 1 (Professional)", "professional", _ARCH, "Architecture", 42, "on_campus", f"{_GA}/architecture/architecture/architecture-march/", 41333, "year"),
    ("Master of Architecture (MArch) — Option 2 (Post-Professional)", "professional", _ARCH, "Architecture", 30, "on_campus", f"{_GA}/architecture/architecture/architecture-march/", 41333, "year"),
    ("Master of Science in Architecture (Option 3)", "masters", _ARCH, "Architecture", 18, "on_campus", f"{_GA}/architecture/architecture/architecture-ms/", None, None),
    # ── The Shepherd School of Music ──
    ("Master of Music", "masters", _MUS, "Music", 24, "on_campus", f"{_GA}/music/music/", None, None),
    ("Doctor of Musical Arts (DMA)", "phd", _MUS, "Music", 60, "on_campus", f"{_GA}/music/music/", None, None),
    ("Artist Diploma", "certificate", _MUS, "Music", 24, "on_campus", "https://music.rice.edu/admissions/shepherd-school-degree-plans", None, None),
    # ── Susanne M. Glasscock School of Continuing Studies ──
    ("Master of Liberal Studies (MLS)", "masters", _GLAS, "Continuing Studies", 24, "hybrid", "https://glasscock.rice.edu/degrees-certificates/degrees/master-liberal-studies", None, None),
    ("Master of Interdisciplinary Studies (MIS)", "masters", _GLAS, "Continuing Studies", 24, "on_campus", "https://glasscock.rice.edu/master-interdisciplinary-studies", None, None),
    ("Master of Arts in Teaching (MAT)", "masters", _GLAS, "Continuing Studies", 36, "hybrid", "https://glasscock.rice.edu/master-arts-teaching", None, None),
]


def _slugify(name: str) -> str:
    s = name.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def _field_from_program_name(name: str) -> str | None:
    if name.startswith("Doctor of Philosophy in "):
        return name[len("Doctor of Philosophy in ") :]
    if name.startswith("Master of Arts in "):
        return name[len("Master of Arts in ") :]
    if name.startswith("Master of Science in "):
        return name[len("Master of Science in ") :]
    if name.startswith("Bachelor of Arts in "):
        return name[len("Bachelor of Arts in ") :]
    if name.startswith("Bachelor of Science in "):
        return name[len("Bachelor of Science in ") :]
    if name.startswith("Bachelor of Music in "):
        return name[len("Bachelor of Music in ") :]
    if name == "Bachelor of Architecture":
        return "Architecture"
    return None


def _field_from_spec(spec: dict) -> str:
    name = spec.get("program_name", "")
    extracted = _field_from_program_name(name)
    if extracted:
        return extracted
    return name


# UG major name → Rice's published owning department (never the bare field echoed as
# ``program_name``; cf. grad ``_GRAD_EXPLICIT`` dept column + General Announcements).
_FIELD_TO_DEPT: dict[str, str] = {
    "Operations Research": "Computational Applied Mathematics and Operations Research",
    "Computational and Applied Mathematics": (
        "Computational Applied Mathematics and Operations Research"
    ),
    "Chemical Engineering": "Chemical and Biomolecular Engineering",
    "Civil Engineering": "Civil and Environmental Engineering",
    "Environmental Engineering": "Civil and Environmental Engineering",
    "Psychology": "Psychological Sciences",
    "Biosciences": "BioSciences",
    "Physics": "Physics and Astronomy",
    "Astronomy": "Physics and Astronomy",
    "Astrophysics": "Physics and Astronomy",
    "Business": "Rice Business",
    "Sport Analytics": "Sport Management",
    "Sport Management": "Sport Management",
    "Art (Studio Art)": "Visual and Dramatic Arts",
    "Architectural Studies": "Architecture",
}


def _department_for(field: str, school: str) -> str:
    """Real Rice owning unit for a field — never ``program_name`` echoed verbatim."""
    if field in _FIELD_TO_DEPT:
        return _FIELD_TO_DEPT[field]
    for name, _dtype, _school, dept, *_rest in _GRAD_EXPLICIT:
        if _field_from_program_name(name) == field:
            return dept
    if school == _BIZ:
        return "Rice Business"
    if school == _ARCH:
        return "Architecture"
    if school == _MUS:
        return "Music"
    if school == _GLAS:
        return "Continuing Studies"
    return field


def _ug_degree_name(major: str, codes: str, school: str) -> str:
    """Conferred undergraduate designation — never a bare field-of-study name."""
    if codes == "BA":
        return f"Bachelor of Arts in {major}"
    if codes == "BS":
        return f"Bachelor of Science in {major}"
    if codes == "BMus":
        return f"Bachelor of Music in {major}"
    if codes == "BA/BArch" and major == "Architecture":
        return "Bachelor of Architecture"
    if codes == "BA/BArch":
        return f"Bachelor of Arts in {major}"
    if codes == "BA/BMus" and major == "Music":
        return "Bachelor of Arts in Music"
    if codes == "BA/BMus":
        return f"Bachelor of Music in {major}"
    if "BS" in codes and school in (_ENG, _NS):
        return f"Bachelor of Science in {major}"
    if "BA" in codes:
        return f"Bachelor of Arts in {major}"
    return f"Bachelor of Arts in {major}"


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    """Drop undergraduate-specific phrasing from a field clause on graduate rows."""
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(
        r"\bundergraduate (major|program)\b", "program", clause, flags=re.I
    )
    return clause


def _rice_description(spec: dict) -> str:
    """Field-specific, per-credential description — never a classification stub.

    Multi-credential fields draw a distinct per-(field, degree_type) body from
    ``FIELD_CRED_DESCRIPTIONS`` so a field's BA / MS / PhD rows no longer share one
    ``FIELD_DESCRIPTIONS`` clause behind a swapped credential frame (REPAIR BACKLOG #3 —
    the run-65 credential-frame + tail-shared field body, gold MIT = 0% shared). Each
    credential level says what THAT degree studies at THAT level. Single-credential fields
    use their unique ``FIELD_DESCRIPTIONS`` clause directly — the redundant
    "Rice offers the … in {field}." classification lead is dropped (gold MIT opens on the
    field fact, never a credential frame).
    """
    field = _field_from_spec(spec)
    dtype = spec["degree_type"]
    cred_body = FIELD_CRED_DESCRIPTIONS.get(field, {}).get(dtype)
    if cred_body:
        body = cred_body
    else:
        clause = FIELD_DESCRIPTIONS.get(field)
        if not clause:
            raise ValueError(
                f"Missing FIELD_DESCRIPTIONS entry for {field!r} ({spec.get('slug')})"
            )
        body = _level_appropriate_clause(clause, dtype)
    fmt = spec.get("delivery_format", "in_person")
    delivery = ""
    if fmt == "online":
        delivery = " Delivered online."
    elif fmt == "hybrid":
        delivery = " Delivered in a hybrid format."
    return f"{body}{delivery}"


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()

    def _add(rec: dict) -> None:
        if rec["slug"] in seen:
            return
        seen.add(rec["slug"])
        out.append(rec)

    for school, majors in _UG_BY_SCHOOL.items():
        for name, codes in majors:
            spec = {
                "slug": f"rice-{_slugify(name)}-ug",
                "school": school,
                "program_name": _ug_degree_name(name, codes, school),
                "degree_type": "bachelors",
                "department": _department_for(name, school),
                "duration_months": 48,
                "delivery_format": "in_person",
            }
            spec["description"] = _rice_description(spec)
            _add(spec)
    suffix = {"phd": "phd", "professional": "prof", "certificate": "cert", "masters": "ms"}
    for name, dtype, school, dept, dur, fmt, website, tuition, tkind in _GRAD_EXPLICIT:
        spec = {
            "slug": f"rice-{_slugify(name)}-{suffix.get(dtype, 'ms')}",
            "school": school,
            "program_name": name,
            "degree_type": dtype,
            "department": dept,
            "duration_months": dur,
            "delivery_format": fmt,
            "website": website,
            "tuition": tuition,
            "tuition_kind": tkind,
        }
        spec["description"] = _rice_description(spec)
        _add(spec)
    return out


PROGRAMS: list[dict] = _build_catalog()
# Normalize residential delivery to the fleet-wide "in_person" value (the catalog tuples use
# "on_campus" for readability); "online"/"hybrid" are preserved.
for _p in PROGRAMS:
    if _p["delivery_format"] == "on_campus":
        _p["delivery_format"] = "in_person"
    _p["description"] = _rice_description(_p)

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
_anti = _anti_stub_analyze(PROGRAMS)
if not _anti.is_clean:
    _catalog_errors.append(f"anti-stub not clean: {_anti.summary()}")
# Frame-stripped shared body: a field's credential siblings (BA / MS / PhD) must NOT share
# a body once a leading credential frame is stripped — the run-65 evasion the leading-prefix
# count in analyze() reads as a false 0 (REPAIR BACKLOG #3 / miss #8 credential-frame). Gold
# MIT = 0; any non-zero here means a field body is stamped across its credential levels.
_frame_shared = _frame_stripped_shared_body(PROGRAMS)
if _frame_shared:
    _catalog_errors.append(
        f"credential siblings share a frame-stripped body on fields: {_frame_shared}"
    )
_dept_echo = [
    p["slug"]
    for p in PROGRAMS
    if p.get("department") and p.get("program_name") == p.get("department")
]
if _dept_echo:
    _catalog_errors.append(
        f"department echoes program_name on {len(_dept_echo)} programs"
    )
if _catalog_errors:
    raise RuntimeError(f"Rice catalog quality gate failed: {_catalog_errors}")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}
_WEBSITE_BY_SLUG: dict[str, str] = {p["slug"]: p["website"] for p in PROGRAMS if p.get("website")}

# Per-program keyword overrides (department/program-naming terms). Programs without an entry
# inherit their school's keywords (still school-scoped).
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "rice-master-of-business-administration-full-time-mba-ms": ["MBA", "Rice Business"],
    "rice-computer-science-ug": ["computer science", "Rice CS"],
    "rice-master-of-computer-science-mcs-rice-online-prof": ["online MCS", "computer science"],
    "rice-master-of-data-science-mds-rice-online-prof": ["data science", "MDS"],
    "rice-doctor-of-philosophy-in-bioengineering-phd": ["bioengineering", "Rice engineering"],
    "rice-master-of-architecture-march-option-1-professional-prof": ["architecture", "MArch"],
    "rice-economics-ug": ["economics", "Rice economics"],
}

# ── Costs ──────────────────────────────────────────────────────────────────
# Published 2025-26 Rice undergraduate figures (Rice Bursar / Common Data Set). Used for
# every residential bachelor's major.
_TUITION_UG = 66540
_UNDERGRAD_COA = 87047
_AVG_NET_PRICE = 13370
_COST_SRC = (
    "Rice Bursar 2025-26 + Rice Common Data Set + College Scorecard (UNITID 227757)",
    "https://bursar.rice.edu/tuition_fee_rates/undergraduate-programs",
)


def _grad_cost(spec: dict) -> dict | None:
    """A verified per-program graduate cost record, or None when tuition is unverified."""
    tuition = spec.get("tuition")
    if tuition is None:
        return None
    kind = spec.get("tuition_kind")
    label = "annual tuition" if kind == "year" else "total program tuition"
    return {
        "tuition_usd": tuition,
        "tuition_basis": kind,
        "funded": False,
        "note": (
            f"Published {label} from the program's official Rice tuition page (2025-26 / "
            "2026-27). Many professional and online programs are billed per credit hour; "
            "research master's and doctoral students are typically funded."
        ),
        "source": "Rice program tuition page / Rice Bursar",
        "source_url": spec.get("website") or _SCHOOL_WEBSITE.get(spec["school"]),
        "year": "2025-26",
    }


# Rice's published 2025-26 standard full-time graduate tuition — the single rate that the
# Wiess (Natural Sciences), Engineering, Humanities, and Social Sciences academic master's
# and PhD programs share (Rice General Announcements, "Tuition, Fees, and Expenses",
# 2025-26: $62,474/yr = $31,237/semester = $3,471/credit hour). It is the matcher-core
# budget signal (REPAIR_BACKLOG run 74 HIGH #2): a funded research doctorate is still stamped
# with the published sticker — funding is carried separately in ``funded``/``note`` — because
# a null/$0 would tell the matcher the whole graduate tier is free and starve every budget
# comparison.
_GRAD_STICKER = 62474
_GRAD_STICKER_SRC = (
    "Rice University General Announcements — Tuition, Fees, and Expenses (2025-26)"
)
_GRAD_STICKER_URL = (
    "https://ga.rice.edu/graduate-students/student-services-organizations/"
    "tuition-fees-expenses/"
)


def _is_funded_academic(spec: dict) -> bool:
    """True for an academic research master's or doctoral program billed at Rice's standard
    full-time graduate tuition (and typically funded with a tuition waiver + stipend).

    Excludes the per-credit / per-program professional and continuing-studies programs:
    the Glasscock School (per credit), and any row that already carries its own verified
    ``tuition`` (set in ``_GRAD_EXPLICIT``) or a ``_COST_BY_SLUG`` override. Professional
    master's (``degree_type == "professional"``) are never funded-academic — they pay a
    published professional rate or honestly omit when Rice bills them per credit."""
    return (
        spec.get("degree_type") in ("phd", "masters")
        and spec.get("school") != _GLAS
        and spec.get("tuition") is None
    )


def _standard_grad_cost(spec: dict) -> dict:
    """Cost record for a funded academic master's / PhD at Rice's published standard
    full-time graduate tuition (the matcher budget reference; funding is a separate signal)."""
    return {
        "tuition_usd": _GRAD_STICKER,
        "tuition_basis": "year",
        "funded": True,
        "note": (
            f"Rice's published 2025-26 standard full-time graduate tuition is ${_GRAD_STICKER:,} "
            "per year ($31,237 per semester / $3,471 per credit hour); this is the matcher's "
            "budget reference. Admitted academic master's and doctoral students at Rice are "
            "typically fully funded with a tuition waiver plus a stipend, so most pay far less "
            "than the published sticker."
        ),
        "source": _GRAD_STICKER_SRC,
        "source_url": _GRAD_STICKER_URL,
        "year": "2025-26",
    }


# ── Outcomes ──────────────────────────────────────────────────────────────
# Rice publishes career outcomes institution-wide (no per-program employment/industry
# split), so every program carries the institution-wide median earnings as its outcomes
# record and omits the program-level employment_rate / top_industries (in _program_standard).
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 89718,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Rice, UNITID 227757)",
    "source_url": "https://collegescorecard.ed.gov/school/?227757-Rice-University",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (first-year) admission via the Common Application / Coalition; Rice is
# test-recommended (effectively test-optional) for the Fall 2026 cycle.
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or Coalition Application", "required": True},
        {"name": "Rice writing supplement", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "School counselor recommendation", "required": True},
        {"name": "One teacher recommendation (a second is optional)", "required": True},
        {"name": "$75 nonrefundable application fee; fee waivers available", "required": True},
        {
            "name": "Standardized test scores (SAT/ACT)",
            "required": False,
            "note": "Rice is test-recommended (effectively test-optional) for the Fall 2026 cycle.",
        },
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 4"},
        {"round": "Regular Decision", "date": "January 4"},
    ],
    "recommendations": {
        "required": 2,
        "note": "A school counselor recommendation plus one teacher recommendation (a second teacher letter is optional).",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Rice Admission — First-Year Applicants", "url": "https://admission.rice.edu/apply/first-year-applicants"}
        ],
    },
    "source": "Rice Undergraduate Admission",
    "source_url": "https://admission.rice.edu/apply/first-year-applicants",
}

# Rice Business Full-Time MBA admission.
_REQ_MBA = {
    "materials": [
        {"name": "Rice Business online application", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "One letter of recommendation", "required": True},
        {"name": "Resume", "required": True},
        {
            "name": "GMAT or GRE scores",
            "required": False,
            "note": "A test waiver is available for qualified applicants.",
        },
        {"name": "Interview (by invitation)", "required": False},
        {"name": "Application fee", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "October"},
        {"round": "Round 2", "date": "January"},
        {"round": "Round 3", "date": "March"},
        {"round": "Round 4", "date": "April"},
    ],
    "recommendations": {
        "required": 1,
        "note": "One letter of recommendation submitted through the Rice Business application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": True,
            "note": "Required for applicants whose first language is not English (waivers apply).",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Rice Business — Full-Time MBA Admissions", "url": "https://business.rice.edu/rice-mba/full-time-mba"}
        ],
    },
    "source": "Jesse H. Jones Graduate School of Business — Full-Time MBA",
    "source_url": "https://business.rice.edu/rice-mba/full-time-mba",
}

# Generic Rice graduate / professional admission set. Each school administers its own
# admissions; the materials below are common, and deadlines vary by program — applicants are
# pointed to the program's own admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most Rice graduate and professional programs require three letters.",
        },
        {
            "name": "Standardized test scores (GRE/GMAT)",
            "required": False,
            "note": "Test requirements vary by program (required, optional or not accepted).",
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "Varies by program — see the program page"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Most Rice graduate and professional programs require three letters of recommendation.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose native language is not English; an exemption "
                "applies to degrees earned where English is the language of instruction."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Rice Graduate and Postdoctoral Studies — Admissions",
                "url": "https://graduate.rice.edu/",
            }
        ],
    },
    "source": "Rice graduate & professional admissions",
    "source_url": "https://graduate.rice.edu/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == "rice-master-of-business-administration-full-time-mba-ms":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# ── Flagship + coverable-program depth ─────────────────────────────────────
_FLAGSHIP = "rice-master-of-business-administration-full-time-mba-ms"

# Rice Business Full-Time MBA employment-report outcomes (Class of 2025).
_MBA_OUTCOMES: dict = {
    "median_salary": 149000,
    "employment_rate": 0.72,
    "top_industries": [
        {"name": "Consulting", "share": 0.24},
        {"name": "Energy", "share": 0.24},
        {"name": "Technology", "share": 0.16},
        {"name": "Financial Services", "share": 0.15},
    ],
    "scope": "program",
    "earnings_timeframe": "base salary at graduation",
    "conditions": (
        "Rice Business Full-Time MBA Class of 2025: reported base salary of $149,000, "
        "average starting salary of $146,000, and average signing bonus of $32,000; 72% "
        "of students accepted job offers from the Rice Business community. Top industries "
        "by share of graduates: consulting 24%, energy 24%, technology 16%, financial "
        "services 15%."
    ),
    "source": "Rice Business — 2025 Full-Time MBA Employment Outcomes Report",
    "source_url": (
        "https://cdn.uconnectlabs.com/wp-content/uploads/sites/99/2026/02/"
        "2025-Full-Time-MBA-Employment-Outcomes-Report-Final-for-Web.pdf"
    ),
}

# Rice Business Full-Time MBA 2025-26 tuition (Rice Bursar published rate).
_MBA_TUITION = 76073
_COST_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tuition_usd": _MBA_TUITION,
        "breakdown": {
            "tuition": _MBA_TUITION,
            "mba_fees": 1230,
        },
        "funded": False,
        "note": (
            "Published 2025-26 Rice Business Full-Time MBA tuition ($76,073 per year) plus "
            "required MBA fees ($1,230). Rice Business reports that 96% of Full-Time MBA "
            "students receive merit-based scholarships with average awards exceeding $80,000."
        ),
        "source": "Rice University Bursar — Business Full-Time MBA",
        "source_url": "https://bursar.rice.edu/tuition_fee_rates/graduate-programs/business/business-full-time-mba",
        "year": "2025-26",
    },
}

_TRACKS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "tracks": [
            "Accounting",
            "Energy",
            "Entrepreneurship",
            "Finance",
            "Healthcare",
            "Marketing",
            "Operations Management",
            "Organizational Behavior",
            "Real Estate",
            "Strategic Management",
        ],
        "source": "Rice Business — Full-Time MBA Specializations",
        "source_url": "https://business.rice.edu/rice-mba/full-time-mba/degree-specializations",
    },
}

_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "cohort_size": "137 students in the entering Full-Time MBA class (Class of 2027)",
        "international_pct": 0.34,
        "note": (
            "Entering Full-Time MBA Class of 2027: 137 students, average GMAT 692, "
            "average GPA 3.4, 5.7 average years of work experience, 34% women, 47% "
            "students of color, 31% underrepresented minorities."
        ),
        "source": "Rice Business — Full-Time MBA Class Profile",
        "source_url": "https://business.rice.edu/rice-mba/full-time-mba/class-profile",
    },
}

_FACULTY_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "lead": [
            {
                "name": "Peter Rodriguez",
                "title": (
                    "Houston Endowment Dean of Jones Graduate School and Virani "
                    "Undergraduate School of Business; Professor of Strategic Management"
                ),
            },
            {
                "name": "Kerry Back",
                "title": "J. Howard Creekmore Professor of Finance and Professor of Economics",
            },
        ],
        "note": (
            "Rice Business faculty spans finance, accounting, marketing, and strategy; "
            "Dean Peter Rodriguez leads the school and finance professor Kerry Back "
            "coordinates the finance area."
        ),
        "directory_url": "https://business.rice.edu/faculty-research/faculty",
    },
}

# Aggregated, cited student-review themes (≥2 third-party sources per coverable program).
_REVIEWS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "summary": (
            "Students and third-party guides describe Rice Business's Full-Time MBA as a "
            "STEM-designated program with world-leading entrepreneurship resources — "
            "The Princeton Review has ranked Jones #1 for graduate entrepreneurship five "
            "years running — and strong Houston energy/consulting placement (Class of 2025 "
            "average starting salary $146,000). Common cautions are that the national MBA "
            "brand is smaller than coastal M7 peers, Houston is less central than NYC/SF "
            "for some finance paths, and the cohort is relatively small."
        ),
        "themes": [
            {
                "label": "Entrepreneurship ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Jones ranked #1 graduate entrepreneurship program by The Princeton "
                    "Review; Liu Idea Lab, OwlSpark, and the Rice Business Plan Competition "
                    "anchor startup activity."
                ),
            },
            {
                "label": "Energy & consulting outcomes",
                "sentiment": "positive",
                "detail": (
                    "Class of 2025: consulting and energy each drew 24% of graduates; "
                    "average starting salary $146K with $32K signing bonus."
                ),
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": (
                    "The Full-Time MBA curriculum is STEM-designated, extending OPT for "
                    "eligible international graduates."
                ),
            },
            {
                "label": "Brand vs. M7 peers",
                "sentiment": "mixed",
                "detail": (
                    "Strong regional outcomes but a smaller national MBA brand than M7 "
                    "schools in some markets."
                ),
            },
            {
                "label": "Houston location",
                "sentiment": "caution",
                "detail": (
                    "Houston's energy and healthcare ecosystems are strengths, but the city "
                    "is less of a traditional finance/consulting hub than NYC or Chicago."
                ),
            },
        ],
        "sources": [
            {
                "label": "Rice Business — 2025 Full-Time MBA Career Highlights",
                "url": "https://business.rice.edu/rice-mba/full-time-mba/career-highlights",
            },
            {
                "label": "Poets&Quants — Meet The Rice Jones MBA Class Of 2025",
                "url": "https://poetsandquants.com/2024/07/14/meet-the-rice-jones-mba-class-of-2025/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "rice-computer-science-ug": {
        "summary": (
            "Students and guides describe Rice's computer science major as rigorous and "
            "research-oriented — Niche ranks it #17 nationally for CS (2026) and College "
            "Factual ranks Rice #20 for computer & information sciences — with B.A., B.S., "
            "and B.S. in Artificial Intelligence paths. Common cautions are competitive "
            "grading, large introductory lectures, and a smaller CS cohort than peer "
            "giants like CMU or MIT."
        ),
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": (
                    "Interdisciplinary research in AI, systems, and computational biology "
                    "with strong faculty in a top-20 CS program."
                ),
            },
            {
                "label": "Flexible degree paths",
                "sentiment": "positive",
                "detail": (
                    "B.A., B.S., and B.S. in Artificial Intelligence majors plus "
                    "interdisciplinary options."
                ),
            },
            {
                "label": "National CS standing",
                "sentiment": "positive",
                "detail": "Niche #17 for undergraduate CS (2026); College Factual #20 nationally.",
            },
            {
                "label": "Competitive atmosphere",
                "sentiment": "caution",
                "detail": (
                    "Selective engineering school with demanding coursework and "
                    "pre-professional pressure."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Computer Science (2026)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
            {
                "label": "Rice Engineering — Computer Science",
                "url": "https://engineering.rice.edu/academics/undergraduate-programs/majors-minors/computer-science",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "rice-master-of-computer-science-mcs-rice-online-prof": {
        "summary": (
            "Students and guides describe Rice's online MCS as a high-touch alternative to "
            "MOOC-style degrees — U.S. News ranked it #3 nationally for online master's in "
            "information technology (2026), up from #10 in 2025 — with small classes and "
            "faculty who know students by name. Common cautions are the part-time pace "
            "(typically 2–3 years), tuition comparable to other top online CS programs, and "
            "less on-campus recruiting than residential MSCS peers."
        ),
        "themes": [
            {
                "label": "National online rank",
                "sentiment": "positive",
                "detail": (
                    "U.S. News #3 for Best Online Master's in Information Technology "
                    "Programs (2026); #1 in Texas."
                ),
            },
            {
                "label": "High-touch online model",
                "sentiment": "positive",
                "detail": (
                    "Not hosted on Coursera/edX; faculty-led courses with personalized "
                    "engagement similar to on-campus MCS."
                ),
            },
            {
                "label": "AI & systems curriculum",
                "sentiment": "positive",
                "detail": (
                    "Covers algorithms, machine learning, AI systems, and software "
                    "engineering for working professionals."
                ),
            },
            {
                "label": "Pace & cost",
                "sentiment": "caution",
                "detail": (
                    "Designed for working professionals over 2–3 years; tuition is "
                    "published per credit on Rice's site."
                ),
            },
        ],
        "sources": [
            {
                "label": "Rice CS — Online MCS ranked #3 by U.S. News (2026)",
                "url": (
                    "https://csweb.rice.edu/news/rice-online-master-computer-science-ranked-3-nation-"
                    "us-news-world-report-2026"
                ),
            },
            {
                "label": "Rice CS — Online Master of Computer Science",
                "url": "https://csweb.rice.edu/academics/graduate-programs/online-mcs",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "rice-master-of-data-science-mds-rice-online-prof": {
        "summary": (
            "Students and guides describe Rice's online MDS as an interactive, project-based "
            "data-science degree — Fortune ranked it among the top 20 online data-science "
            "programs (2024) and College Factual ranks Rice among the best computer & "
            "information sciences master's programs — with real datasets from companies and "
            "nonprofits. Common cautions are the newer online format (launched after MCS), "
            "part-time completion timelines, and less third-party review coverage than the "
            "flagship online MCS."
        ),
        "themes": [
            {
                "label": "Project-based curriculum",
                "sentiment": "positive",
                "detail": (
                    "Students work with real-world datasets from companies, nonprofits, "
                    "and government partners."
                ),
            },
            {
                "label": "National recognition",
                "sentiment": "positive",
                "detail": (
                    "Fortune top-20 online data-science program (2024); College Factual "
                    "ranks Rice CS master's programs highly."
                ),
            },
            {
                "label": "AI & ML focus",
                "sentiment": "positive",
                "detail": (
                    "Prepares graduates for data science, analytics, and AI/machine-learning "
                    "roles."
                ),
            },
            {
                "label": "Limited public reviews",
                "sentiment": "mixed",
                "detail": (
                    "Fewer independent student-review sites cover MDS than the longer-"
                    "running online MCS program."
                ),
            },
        ],
        "sources": [
            {
                "label": "Rice CS — Online Master of Data Science",
                "url": "https://csweb.rice.edu/academics/graduate-programs/online-mds",
            },
            {
                "label": "Rice News — Online programs climb in U.S. News rankings (2026)",
                "url": (
                    "https://news.rice.edu/news/2026/rice-online-programs-climb-us-news-world-"
                    "report-rankings-led-top-tier-computer-science"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "rice-master-of-architecture-march-option-1-professional-prof": {
        "summary": (
            "Students and guides describe Rice's NAAB-accredited M.Arch as a small, rigorous "
            "studio program — Niche ranked Rice #1 for architecture majors (2023) and "
            "Black Spectacles cites a 76% ARE pass rate — with a Paris campus and Houston's "
            "architectural diversity as differentiators. Common cautions are the intensive "
            "studio workload, limited cohort size, and Rice's 2022 decision to distance "
            "itself from DesignIntelligence rankings."
        ),
        "themes": [
            {
                "label": "Small cohort & faculty access",
                "sentiment": "positive",
                "detail": (
                    "Highly personalized instruction within a top-20 research university; "
                    "NAAB-accredited and STEM-designated."
                ),
            },
            {
                "label": "Licensure outcomes",
                "sentiment": "positive",
                "detail": (
                    "Black Spectacles cites a 76% ARE pass rate, among the highest "
                    "nationally."
                ),
            },
            {
                "label": "Global studio opportunities",
                "sentiment": "positive",
                "detail": (
                    "Paris campus semester and Houston's diverse built environment "
                    "provide real-world design context."
                ),
            },
            {
                "label": "Intensive studio culture",
                "sentiment": "caution",
                "detail": (
                    "Seven-semester professional track demands sustained studio work "
                    "and crit-heavy semesters."
                ),
            },
        ],
        "sources": [
            {
                "label": "Rice School of Architecture — Graduate",
                "url": "https://arch.rice.edu/academics/graduate",
            },
            {
                "label": "Black Spectacles — Top M.Arch Programs (ARE pass rates)",
                "url": "https://www.blackspectacles.com/blog/top-10-masters-of-architecture-programs-in-the-us",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "rice-economics-ug": {
        "summary": (
            "Students and guides describe Rice's economics major as analytically rigorous — "
            "Niche ranks it #18 nationally for economics (2026) — within a small "
            "undergraduate college where economics is the largest social-sciences major. "
            "Common cautions are that Rice lacks a standalone undergraduate business school "
            "(business is a minor/ concentration), quantitative courses can be demanding, "
            "and the Houston finance recruiting network is smaller than coastal peers."
        ),
        "themes": [
            {
                "label": "National economics standing",
                "sentiment": "positive",
                "detail": "Niche #18 Best Colleges for Economics in America (2026).",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": (
                    "School of Social Sciences emphasizes econometrics and data-driven "
                    "analysis with research-active faculty."
                ),
            },
            {
                "label": "Small-college experience",
                "sentiment": "positive",
                "detail": (
                    "6:1 student-faculty ratio and residential-college system support "
                    "close faculty access."
                ),
            },
            {
                "label": "Finance recruiting footprint",
                "sentiment": "caution",
                "detail": (
                    "Strong Houston energy/consulting ties but fewer Wall Street "
                    "on-campus recruiters than coastal Ivies."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Economics (2026)",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
            {
                "label": "Rice Economics — Department News",
                "url": "https://economics.rice.edu/news/social-sciences-undergraduate-majors-see-rise-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}


# Lovett Hall statue leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]``.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Rice to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Rice is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1912
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.rice.edu"
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
        # Every school gets a working feed (the verified Rice events RSS + iCalendar, filtered
        # to school-relevant items by keywords) so its Events & Updates tab populates —
        # overwriting any stale value on a pre-existing row.
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
    # Rice publishes no per-program employment report or industry breakdown (its career
    # outcomes are reported institution-wide, captured at the institution level), so every
    # program except the Full-Time MBA omits the program-level employment rate and top
    # industries.
    if slug != _FLAGSHIP:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    # Per-credit professional / continuing-studies programs without a verified annual figure
    # omit tuition_usd (their cost_data carries a sourced per-credit record). Funded academic
    # master's / PhD now carry Rice's published standard graduate sticker, so they are NOT
    # omitted (REPAIR_BACKLOG run 74 HIGH #2 — matcher-core budget signal).
    if (
        spec.get("degree_type") != "bachelors"
        and slug not in _COST_BY_SLUG
        and spec.get("tuition") is None
        and not _is_funded_academic(spec)
    ):
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    # content_sources is set on every program (school feed + program keywords), never omitted.
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
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.department = spec.get("department")
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_SCHOOL_FEED_SPEC[spec["school"]]["keywords"])
        p.content_sources = _program_content(spec["school"], _kw)
        # Cost precedence: published Rice College rates for bachelor's majors → a verified
        # per-program graduate tuition → a sourced "see the program page" record (tuition_usd
        # recorded omitted, never guessed and never set to the undergraduate rate).
        if spec["degree_type"] == "bachelors":
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
                    "Published 2025-26 Rice undergraduate tuition with the billed cost of "
                    "attendance and the College Scorecard average net price. Rice meets 100% "
                    "of demonstrated financial need through The Rice Investment, so most "
                    "families pay far less than the sticker price (average net price ≈ $13,000)."
                ),
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2025-26",
            }
        else:
            grad_cost = _grad_cost(spec)
            cost_override = _COST_BY_SLUG.get(slug)
            if cost_override is not None:
                p.tuition = cost_override["tuition_usd"]
                p.cost_data = cost_override
            elif grad_cost is not None:
                p.tuition = grad_cost["tuition_usd"]
                p.cost_data = grad_cost
            elif _is_funded_academic(spec):
                standard_cost = _standard_grad_cost(spec)
                p.tuition = standard_cost["tuition_usd"]
                p.cost_data = standard_cost
            else:
                p.tuition = None
                p.cost_data = {
                    "note": (
                        "Tuition for this professional/continuing-studies program is billed "
                        "per credit hour and varies with the program's credit requirement, so "
                        "no single verified annual figure is published here; see the program's "
                        "official Rice tuition page."
                    ),
                    "source": "Rice University — program tuition page",
                    "source_url": spec.get("website") or _SCHOOL_WEBSITE.get(spec["school"]),
                }
        p.application_requirements = _requirements_for(spec)
        if slug == _FLAGSHIP:
            outcomes = dict(_MBA_OUTCOMES)
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = None
        p.highlights = None
        p.application_deadline = (
            date(2027, 1, 4) if spec["degree_type"] == "bachelors" else None
        )
    session.flush()
    # Reconcile legacy Rice programs (slug not in the canonical set): delete when
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
