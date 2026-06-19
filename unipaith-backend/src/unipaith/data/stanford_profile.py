"""Canonical Stanford University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard · Stanford
Common Data Set / IRDS · Stanford FY2024 Annual Financial Report · QS · Times
Higher Education · U.S. News · each school's official dean's office · the Stanford
GSB MBA Employment Report). ``apply(session)`` idempotently enriches the Stanford
institution row, upserts the seven real schools, and builds Stanford's program
catalog across them.

It **flushes but does not commit** — the caller (the Alembic data migration, the
CLI script, or the dev seed) owns the transaction. It is a **no-op** (returns
``False``) when Stanford is absent, so it is safe to run against a fresh or CI
database. Re-running is safe: schools key off ``(institution_id, name)`` and
programs off ``slug``; stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``harvard_profile`` so the migration, the
standalone script, and the dev seed all agree (DRY). Every figure traces to a
public, citable source; anything that could not be verified from a first-party or
two-independent-source basis is **omitted** (recorded in the relevant
``_standard.omitted`` list), never guessed. The Stanford GSB MBA is the
fully-enriched flagship program (its own employment report, class profile,
admissions, faculty, and aggregated reviews), mirroring MIT Sloan's MBAn in the
reference instance.

Depth pass (2026-06-15, stanfordprof6): merged ``DEPTH_REVIEWS`` for 28 coverable
programs (38/38 total coverable reviews).

Description repair (2026-06-19, stanfordprof11): replaces 150 "Catalog entry <hex>:" build-
artifact descriptions with verified per-credential discipline definitions (same model as
Michigan michprof4 / UW uwdefab1). Prior stanfordprof10 de-fabricated names/departments but
left the machine-assembly descriptions live.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.stanford_catalog_descriptions import PROGRAMS as _CATALOG_PROGRAMS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze

INSTITUTION_NAME = "Stanford University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-19"


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
    # Stanford does not publish a clean university-wide undergraduate
    # first-destination ("employed or continuing education") rate; omitted rather
    # than inferred. Per-school placement (e.g. GSB) is captured at program level.
    "school_outcomes.employed_or_continuing_ed",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank` (labelled via the
# frontend `rankingLabel` map, which already knows these keys).
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
    # Stanford is accredited by the WASC Senior College and University Commission.
    "accreditor": "WSCUC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026 (released 2025-06): MIT 1, Imperial 2,
    # Stanford 3.
    "qs_world_university_rankings": {"rank": 3, "year": 2026},
    # THE World University Rankings 2025 (released 2024-10): Stanford 6.
    "times_higher_education": {"rank": 6, "year": 2025},
    # U.S. News Best National Universities 2026 (released 2025-09): Princeton 1,
    # MIT 2, Harvard 3, Stanford/Yale 4.
    "us_news_national": {"rank": 4, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below
# is complete, so a shallow merge is correct. Figures are College Scorecard
# (UNITID 243744) cross-checked against Stanford's Common Data Set 2024-25 where
# both publish the metric (admit rate, retention, 6-year graduation all agree).
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 (Class of 2028): 2,067 offers / 57,326 applications = 3.61%.
    "admit_rate": 0.0361,
    "avg_net_price": 13807,
    "median_earnings_10yr": 124080,
    "completion_rate_4yr_150pct": 0.9192,
    "retention_rate_first_year": 0.982,
    "graduation_rate_6yr": 0.919,
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    "financial_aid": {
        "pell_grant_rate": 0.1916,
        "federal_loan_rate": 0.062,
        "median_debt_completers": 12000,
        "cost_of_attendance": 87833,
        # 2025-26 aid policy (Stanford Financial Aid): families with annual income
        # below $150,000 (and typical assets) pay no tuition; below $100,000 pay no
        # tuition, room, or board.
        "tuition_free_income_threshold_usd": 150000,
        "room_board_free_income_threshold_usd": 100000,
    },
    "demographics": {
        "white": 0.2299,
        "black": 0.0741,
        "hispanic": 0.1706,
        "asian": 0.2873,
        "women": 0.5163,
    },
    # Stanford Main Quad / central campus.
    "location": {"lat": 37.4275, "lng": -122.1697},
    "campus_basics": {"location": "Stanford, California (San Francisco Bay Area)"},
    "top_employer_industries": [
        "Technology",
        "Finance",
        "Consulting",
        "Healthcare & medicine",
        "Education",
        "Government & public service",
    ],
    "scale": {
        # Full-time faculty (IPEDS-derived, via CollegeFactual); Stanford's Academic
        # Council professoriate is reported at ~2,400 (Stanford Facts).
        "faculty_count": 2345,
        # Widely and consistently published (U.S. News, Stanford Facts).
        "student_faculty_ratio": "5:1",
        # Endowment value at FY end Aug 31, 2024 (Stanford FY2024 Annual Financial
        # Report; College Scorecard end-of-year value agrees at $37.63B).
        "endowment_usd": 37600000000,
        "campus_acres": 8180,
    },
    "research": {
        "labs": [
            "SLAC National Accelerator Laboratory",
            "Hoover Institution",
            "Stanford Institute for Human-Centered AI (HAI)",
            "Bio-X",
            "Wu Tsai Neurosciences Institute",
            "Woods Institute for the Environment",
            "Precourt Institute for Energy",
            "Freeman Spogli Institute for International Studies (FSI)",
            "Stanford Institute for Economic Policy Research (SIEPR)",
        ],
        "areas": [
            "AI & computing",
            "Biosciences & medicine",
            "Climate, energy & sustainability",
            "Economics & public policy",
            "Engineering & the physical sciences",
            "Humanities & social sciences",
        ],
        "lab_links": {
            "SLAC National Accelerator Laboratory": "https://www6.slac.stanford.edu/",
            "Hoover Institution": "https://www.hoover.org/",
            "Stanford Institute for Human-Centered AI (HAI)": "https://hai.stanford.edu/",
            "Bio-X": "https://biox.stanford.edu/",
            "Wu Tsai Neurosciences Institute": "https://neuroscience.stanford.edu/",
            "Woods Institute for the Environment": "https://woods.stanford.edu/",
            "Precourt Institute for Energy": "https://energy.stanford.edu/",
            "Freeman Spogli Institute for International Studies (FSI)": "https://fsi.stanford.edu/",
            "Stanford Institute for Economic Policy Research (SIEPR)": "https://siepr.stanford.edu/",
        },
    },
    "campus_life": {
        # Stanford sponsors 36 varsity sports — among the most of any U.S.
        # university — and competes in NCAA Division I (Atlantic Coast Conference
        # since August 2024).
        "varsity_sports": 36,
        "athletics_division": "NCAA Division I (ACC)",
        "housing": "Guaranteed all four undergraduate years",
        "resources": [
            {"label": "Residential Education", "url": "https://resed.stanford.edu/"},
            {"label": "Athletics (Stanford Cardinal)", "url": "https://gostanford.com/"},
            {"label": "Arts at Stanford", "url": "https://arts.stanford.edu/"},
        ],
    },
    # Verified outdoor campus gallery (Wikimedia Commons API extmetadata, 2026-06-15).
    # Main Quad leads the institution hero; each file carries a verified author + license.
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/"
                "Stanford_University_Main_Quad_-_7_June_2009.jpg/"
                "1920px-Stanford_University_Main_Quad_-_7_June_2009.jpg"
            ),
            "credit": "Wikimedia Commons / Steve Jurvetson (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/"
                "Stanford_University_from_Hoover_Tower_January_2013_panorama.jpg/"
                "1920px-Stanford_University_from_Hoover_Tower_January_2013_panorama.jpg"
            ),
            "credit": "Wikimedia Commons / King of Hearts (CC BY-SA 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/"
                "Stanford_Memorial_Church_May_2011_HDR_1.jpg/"
                "1920px-Stanford_Memorial_Church_May_2011_HDR_1.jpg"
            ),
            "credit": "Wikimedia Commons / King of Hearts (CC BY-SA 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/"
                "Stanford_University_Aerial_View.jpg/"
                "1920px-Stanford_University_Aerial_View.jpg"
            ),
            "credit": "Wikimedia Commons / Mark Leschinsky (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/"
                "Stanford_University_campus_in_2016.jpg/"
                "1920px-Stanford_University_campus_in_2016.jpg"
            ),
            "credit": "Wikimedia Commons / Frank Schulenburg (CC BY-SA 4.0)",
        },
    ],
    # Main Quad leads the hero; see ``campus_photos[0]``.
    "media_credit": "Wikimedia Commons / Steve Jurvetson (CC BY 2.0)",
    "flagship": {
        # Total degree-seeking enrollment, College Scorecard (UNITID 243744):
        # 7,554 undergraduate + 10,721 graduate/professional.
        "enrollment_total": 18275,
        "applicants": 57326,
        "admits": 2067,
        "admissions_cycle": "Class of 2028 (Common Data Set 2024-25)",
        # Stanford is associated with 58 Nobel laureates (faculty + alumni).
        "nobel_laureates": 58,
        "founded_year": 1885,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Stanford, UNITID 243744)",
            "url": "https://collegescorecard.ed.gov/school/?243744",
        },
        {
            "label": "Stanford Common Data Set (Institutional Research & Decision Support)",
            "url": "https://irds.stanford.edu/data-findings/cds",
        },
        {
            "label": "Final enrollment data for Class of 2028 (Stanford Report)",
            "url": (
                "https://news.stanford.edu/stories/2025/01/"
                "final-enrollment-data-for-class-of-2028-reported-in-common-data-set"
            ),
        },
        {
            "label": "Stanford FY2024 Annual Financial Report (endowment, Aug 31, 2024)",
            "url": (
                "https://bondholder-information.stanford.edu/sites/g/files/"
                "sbiybj21416/files/media/file/fy24-annual-financial-report_0.pdf"
            ),
        },
        {"label": "Stanford Facts", "url": "https://facts.stanford.edu/"},
        {
            "label": "QS World University Rankings 2026",
            "url": "https://www.topuniversities.com/universities/stanford-university",
        },
        {
            "label": "Times Higher Education World University Rankings",
            "url": "https://www.timeshighereducation.com/world-university-rankings/stanford-university",
        },
        {
            "label": "U.S. News — Stanford University",
            "url": "https://www.usnews.com/best-colleges/stanford-university-1305",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it
# "Undergraduates"); the total (18,275) lives in flagship.enrollment_total and
# renders as "Total enrollment". 7,554 = College Scorecard degree-seeking
# undergraduates (UNITID 243744).
UNDERGRAD_COUNT = 7554

DESCRIPTION = (
    "Stanford University is a private research university in Stanford, California, "
    "on an 8,180-acre campus — one of the largest in the nation — at the heart of "
    "Silicon Valley on the San Francisco Peninsula. Founded in 1885 by Leland and "
    "Jane Stanford in memory of their only child and opened to students in 1891, "
    "Stanford is organized into seven degree-granting schools.\n\n"
    "Stanford is organized into seven schools: the School of Humanities and "
    "Sciences; the School of Engineering; the Stanford Doerr School of "
    "Sustainability (opened in 2022, the university's first new school in 70 "
    "years); the Graduate School of Business; the Graduate School of Education; "
    "Stanford Law School; and the School of Medicine. Roughly 7,600 "
    "undergraduates and more than 10,000 graduate and professional students study "
    "across these units, supported by one of the largest research enterprises of "
    "any U.S. university — including SLAC National Accelerator Laboratory, the "
    "Hoover Institution, and the Stanford Institute for Human-Centered AI.\n\n"
    "Stanford ranks among the very best universities in the world — No. 3 globally "
    "by QS, and No. 4 on the U.S. News national-universities list — and is "
    "associated with 58 Nobel laureates. Its faculty and alumni have founded a "
    "remarkable share of the modern technology industry, from Hewlett-Packard and "
    "Google to Netflix and Nvidia.\n\n"
    "A rigorous education across the sciences, engineering, humanities, and the "
    "professions — paired with need-based aid that holds the average net price "
    "near $14,000 a year and waives tuition entirely for families earning under "
    "$150,000 — produces graduates with a median income of roughly $124,000 a "
    "decade after entry."
)

# ── The seven real schools (in display order) ──────────────────────────────
_HS = "School of Humanities and Sciences"
_ENG = "School of Engineering"
_SUS = "Stanford Doerr School of Sustainability"
_GSB = "Graduate School of Business"
_GSE = "Graduate School of Education"
_LAW = "Stanford Law School"
_MED = "School of Medicine"

SCHOOLS: list[dict] = [
    {
        "name": _HS,
        "sort_order": 1,
        "description": (
            "Stanford's largest school and the center of its liberal-arts education — "
            "spanning the humanities, the natural sciences, the social sciences, and "
            "the arts across 24 departments and dozens of interdisciplinary programs, "
            "from economics, mathematics, and physics to philosophy, history, and "
            "psychology."
        ),
    },
    {
        "name": _ENG,
        "sort_order": 2,
        "description": (
            "Founded in 1925 and now in its second century, Stanford Engineering is a "
            "global engine of Silicon Valley innovation — nine departments spanning "
            "computer science, electrical engineering, bioengineering, and "
            "aeronautics & astronautics, with a culture that has spun out a remarkable "
            "share of the technology industry."
        ),
    },
    {
        "name": _SUS,
        "sort_order": 3,
        "description": (
            "The Stanford Doerr School of Sustainability — opened in 2022 as the "
            "university's first new school in 70 years, seeded by a $1.1 billion gift "
            "from John and Ann Doerr — tackles climate and sustainability across the "
            "Earth, energy, and environmental sciences, paired with a Sustainability "
            "Accelerator that moves research into real-world policy and technology."
        ),
    },
    {
        "name": _GSB,
        "sort_order": 4,
        "description": (
            "One of the world's leading and most selective business schools, founded "
            "in 1925 at the urging of trustee (and future U.S. President) Herbert "
            "Hoover. Its mission — to 'change lives, change organizations, change the "
            "world' — is pursued through the MBA, the mid-career MSx, a research PhD, "
            "and executive education, with deep strengths in entrepreneurship, "
            "finance, and organizational behavior."
        ),
    },
    {
        "name": _GSE,
        "sort_order": 5,
        "description": (
            "Stanford Graduate School of Education, founded in 1917, is consistently "
            "ranked among the top schools of education in the country — advancing "
            "learning science, education policy, and equity through master's, "
            "doctoral, and teacher-education programs closely tied to its research "
            "centers."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 6,
        "description": (
            "Stanford Law School, whose roots reach back to 1893, is one of the "
            "nation's premier law schools — small by design and famous for its "
            "interdisciplinary, technology-and-policy orientation, joint degrees, and "
            "clinical programs at the intersection of law, business, and engineering."
        ),
    },
    {
        "name": _MED,
        "sort_order": 7,
        "description": (
            "Stanford School of Medicine, established at Stanford in 1908, is a leader "
            "in biomedical research, education, and patient care — pioneering "
            "discoveries from the first successful human heart-lung transplant to "
            "advances in genomics, immunology, and bioengineering, in close "
            "partnership with Stanford Health Care and Stanford Children's Health."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _HS: "https://humsci.stanford.edu/",
    _ENG: "https://engineering.stanford.edu/",
    _SUS: "https://sustainability.stanford.edu/",
    _GSB: "https://www.gsb.stanford.edu/",
    _GSE: "https://ed.stanford.edu/",
    _LAW: "https://law.stanford.edu/",
    _MED: "https://med.stanford.edu/",
}

# Rich, sourced About-tab content per school. Deans + endowed-chair titles are
# quoted from each school's official dean's-office page (verified 2026-06-10);
# founding years from each school's official history / Wikipedia. Faculty lists
# are short, curated rosters of prominent, clearly-current Stanford faculty.
_ABOUT_DETAIL: dict[str, dict] = {
    _HS: {
        "founded": 1948,
        "leadership": "Debra Satz — Vernon R. and Lysbeth Warren Anderson Dean (since 2018)",
        "faculty": [
            {
                "name": "Matthew Gentzkow",
                "title": "Professor of Economics",
                "focus": "Media, markets & applied economics (2014 Clark Medal)",
            },
            {
                "name": "Carol Dweck",
                "title": "Lewis & Virginia Eaton Professor of Psychology",
                "focus": "Motivation and the psychology of mindset",
            },
        ],
        "research_centers": [
            "Stanford Institute for Economic Policy Research (SIEPR)",
            "Stanford Humanities Center",
            "Center for the Study of Language and Information (CSLI)",
        ],
        "named_for": None,
        "source": {
            "label": "Stanford H&S — Dean's Office / History",
            "url": "https://humsci.stanford.edu/about/hs-history",
        },
    },
    _ENG: {
        "founded": 1925,
        "leadership": ("Jennifer Widom — Frederick Emmons Terman Dean of Engineering (since 2017)"),
        "faculty": [
            {
                "name": "Fei-Fei Li",
                "title": "Sequoia Professor of Computer Science",
                "focus": "Computer vision & AI; co-director, Stanford HAI",
            },
            {
                "name": "Christopher Manning",
                "title": "Thomas M. Siebel Professor in Machine Learning",
                "focus": "Natural language processing; director, Stanford AI Lab",
            },
        ],
        "research_centers": [
            "Stanford Artificial Intelligence Laboratory (SAIL)",
            "Stanford Institute for Human-Centered AI (HAI)",
            "SystemX Alliance",
        ],
        "named_for": None,
        "source": {
            "label": "Stanford Engineering — Dean's Office",
            "url": "https://engineering.stanford.edu/about/dean",
        },
    },
    _SUS: {
        "founded": 2022,
        "leadership": "Arun Majumdar — inaugural Dean; Jay Precourt Provostial Chair Professor",
        "faculty": [
            {
                "name": "Rob Jackson",
                "title": "Michelle and Kevin Douglas Provostial Professor",
                "focus": "Global carbon cycle & climate; chairs the Global Carbon Project",
            },
            {
                "name": "Noah Diffenbaugh",
                "title": "Kara J Foundation Professor",
                "focus": "Climate dynamics, extremes & impacts",
            },
        ],
        "research_centers": [
            "Woods Institute for the Environment",
            "Precourt Institute for Energy",
            "Stanford Sustainability Accelerator",
        ],
        "named_for": (
            "John and Ann Doerr, whose $1.1 billion founding gift in 2022 was the "
            "largest in Stanford's history"
        ),
        "source": {
            "label": "Stanford Doerr School of Sustainability — Leadership",
            "url": "https://sustainability.stanford.edu/our-community/leadership/dean-arun-majumdar",
        },
    },
    _GSB: {
        "founded": 1925,
        "leadership": (
            "Sarah Soule — Philip H. Knight Professor and Dean (since 2025; the "
            "school's first woman dean)"
        ),
        "faculty": [
            {
                "name": "Susan Athey",
                "title": "Economics of Technology Professor",
                "focus": "Marketplace design, machine learning & economics",
            },
            {
                "name": "Brian Lowery",
                "title": "Walter Kenneth Kilpatrick Professor of Organizational Behavior",
                "focus": "Social identity, inequality & leadership",
            },
        ],
        "research_centers": [
            "Center for Entrepreneurial Studies",
            "Center for Social Innovation",
            "Stanford Institute for Innovation in Developing Economies (SEED)",
        ],
        "named_for": None,
        "source": {
            "label": "Sarah Soule appointed dean of the Stanford GSB (Stanford Report)",
            "url": "https://news.stanford.edu/stories/2025/01/sarah-soule-appointed-dean-of-the-stanford-graduate-school-of-business",
        },
    },
    _GSE: {
        "founded": 1917,
        "leadership": "Daniel Schwartz — I. James Quillen Dean of the Graduate School of Education",
        "faculty": [
            {
                "name": "Sean Reardon",
                "title": "Professor of Poverty and Inequality in Education",
                "focus": "Educational opportunity, segregation & achievement gaps",
            },
            {
                "name": "Linda Darling-Hammond",
                "title": "Charles E. Ducommun Professor of Education, Emeritus",
                "focus": "Teaching quality, equity & education policy",
            },
        ],
        "research_centers": [
            "Stanford Center for Education Policy Analysis (CEPA)",
            "Graduate School of Education's Center to Support Excellence in Teaching (CSET)",
            "Stanford Accelerator for Learning",
        ],
        "named_for": None,
        "source": {"label": "Stanford GSE — Dean", "url": "https://ed.stanford.edu/faculty/danls"},
    },
    _LAW: {
        "founded": 1893,
        "leadership": "George Triantis — Charles J. Meyers Professor of Law and Dean (since 2024)",
        "faculty": [
            {
                "name": "Mark Lemley",
                "title": "William H. Neukom Professor of Law",
                "focus": "Intellectual property & technology law",
            },
            {
                "name": "Pamela Karlan",
                "title": "Kenneth and Harle Montgomery Professor of Public Interest Law",
                "focus": "Constitutional law & voting rights",
            },
        ],
        "research_centers": [
            "Stanford Center for Internet and Society",
            "Stanford Criminal Justice Center",
            "Rock Center for Corporate Governance",
        ],
        "named_for": None,
        "source": {
            "label": "George Triantis named dean of Stanford Law School (Stanford Report)",
            "url": "https://news.stanford.edu/stories/2024/03/george-triantis-appointed-dean-of-stanford-law-school",
        },
    },
    _MED: {
        "founded": 1908,
        "leadership": (
            "Lloyd B. Minor, MD — Carl and Elizabeth Naumann Dean; VP for Medical Affairs"
        ),
        # Individual faculty rosters for the School of Medicine were not verified
        # to a single citable source at author time and are omitted; the school's
        # research institutes (below) are first-party verifiable.
        "research_centers": [
            "Stanford Cancer Institute",
            "Stanford Cardiovascular Institute",
            "Wu Tsai Neurosciences Institute",
            "Maternal & Child Health Research Institute",
            "Stanford Bio-X",
        ],
        "named_for": None,
        "source": {
            "label": "Stanford Medicine — Leadership",
            "url": "https://med.stanford.edu/school/leadership/dean.html",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each
# school node's _standard.omitted.
_ABOUT_OMITTED: dict[str, list[str]] = {
    _MED: ["about_detail.faculty"],
}

# ── Per-node content feeds (so EVERY school + program has a populated Events &
# Updates tab, not just the GSB/MBA flagship) ─────────────────────────────────
# Stanford Report RSS (news.stanford.edu/feed/) is Cloudflare-gated to server
# fetches (HTTP 403, verified 2026-06-14), so every node routes through the
# verified, server-fetchable Stanford Law School RSS below — filtered by school/
# program keywords (the Columbia/MIT pattern). Campus events use the official
# Stanford Events iCal (verified 2026-06-14).
_LAW_RSS = "https://law.stanford.edu/feed/"
_STANFORD_EVENTS_ICS = {"url": "https://events.stanford.edu/calendar.ics", "type": "ical"}
_SOCIAL_STANFORD = {
    "instagram": "https://www.instagram.com/stanford/",
    "linkedin": "https://www.linkedin.com/school/stanford-university/",
    "x": "https://x.com/stanford",
    "youtube": "https://www.youtube.com/stanford",
    "facebook": "https://www.facebook.com/stanford",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _LAW_RSS,
    "news_url": "https://www.stanford.edu/",
    "news_curated": False,
    "events_feed": dict(_STANFORD_EVENTS_ICS),
    "social": dict(_SOCIAL_STANFORD),
}

# Keywords filter the shared Stanford feed to school-relevant items (the MIT/MBAn
# pattern). GSB carries its own Insights RSS when available.
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _HS: [
        "humanities",
        "sciences",
        "economics",
        "mathematics",
        "physics",
        "psychology",
        "undergraduate",
    ],
    _ENG: ["engineering", "computer science", "electrical engineering", "robotics", "AI"],
    _SUS: ["sustainability", "climate", "energy", "earth", "environment", "Doerr"],
    _GSB: ["gsb", "stanford gsb", "graduate school of business", "MBA", "business"],
    _GSE: ["education", "GSE", "teaching", "learning sciences"],
    _LAW: ["law school", "legal", "Stanford Law", "jurisprudence"],
    _MED: ["medicine", "medical school", "Stanford Medicine", "health", "clinical"],
}

_KW_STOP = {
    "and", "of", "the", "in", "for", "with", "science", "sciences", "engineering",
    "master", "doctor", "bachelor", "studies", "general",
}


def _school_content(name: str) -> dict:
    """A school's content_sources: verified RSS + events calendar filtered by keywords."""
    return {
        "news_rss": _LAW_RSS,
        "news_url": _SCHOOL_WEBSITE.get(name, "https://www.stanford.edu"),
        "news_curated": False,
        "events_feed": dict(_STANFORD_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_STANFORD),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_KEYWORDS[spec["school"]])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# Stanford GSB keyword-relevant feeds + official social links (the standard-setting
# school, mirroring how MIT Sloan carries its own feeds in the reference instance).
_GSB_CONTENT: dict = {
    "news_rss": _LAW_RSS,
    "news_url": "https://www.gsb.stanford.edu/insights",
    "news_curated": False,
    "events_feed": dict(_STANFORD_EVENTS_ICS),
    "keywords": ["gsb", "stanford gsb", "graduate school of business"],
    "social": {
        "instagram": "https://www.instagram.com/stanfordgsb/",
        "linkedin": "https://www.linkedin.com/school/stanford-graduate-school-of-business/",
        "x": "https://x.com/StanfordGSB",
        "youtube": "https://www.youtube.com/user/stanfordbusiness",
        "facebook": "https://www.facebook.com/StanfordGSB",
    },
}

# MBA keyword-relevant feeds (the flagship program), inheriting GSB's socials.
_MBA_CONTENT: dict = {
    "news_rss": _LAW_RSS,
    "news_url": "https://www.gsb.stanford.edu/programs/mba",
    "news_curated": False,
    "events_feed": dict(_STANFORD_EVENTS_ICS),
    "keywords": ["mba", "stanford mba", "gsb"],
    "social": _GSB_CONTENT["social"],
}

_FLAGSHIP = "stanford-mba"

# ── The program catalog (verified names, departments, descriptions) ─────────
PROGRAMS: list[dict] = [dict(p) for p in _CATALOG_PROGRAMS]
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}


def _assert_anti_stub_clean(programs: list[dict]) -> None:
    """Every Stanford description must score the gold-MIT zero on anti-stub metrics."""
    from unipaith.profile_standard.anti_stub import machine_artifacts

    report = analyze(programs)
    arts = machine_artifacts(programs)
    if not report.is_clean or arts:
        raise ValueError(
            f"Stanford catalog anti-stub gate failed: {report.summary()} artifacts={len(arts)}"
        )


_assert_anti_stub_clean(PROGRAMS)
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# Official program-page URLs (verified to resolve at author time).
_WEBSITE_BY_SLUG: dict[str, str] = {
    "stanford-cs-ms": "https://www.cs.stanford.edu/admissions/masters-admissions",
    "stanford-cs-bs": "https://www.cs.stanford.edu/admissions/undergraduate-admissions",
    "stanford-cs-phd": "https://www.cs.stanford.edu/admissions/phd-admissions",
    "stanford-ee-ms": "https://ee.stanford.edu/academics/graduate",
    "stanford-me-ms": "https://me.stanford.edu/academics-admissions/graduate-program",
    "stanford-me-bs": "https://me.stanford.edu/academics-admissions/undergraduate-program",
    "stanford-cee-ms": "https://cee.stanford.edu/academics-admissions/graduate-programs",
    "stanford-aa-ms": "https://aa.stanford.edu/academicsadmission/graduate-degree-programs",
    "stanford-bioe-bs": "https://bioengineering.stanford.edu/academics/undergraduate-program",
    "stanford-mse-ms": "https://msande.stanford.edu/academics-admissions/graduate/ms",
    "stanford-economics-bs": "https://economics.stanford.edu/undergraduate",
    "stanford-economics-phd": "https://economics.stanford.edu/graduate",
    "stanford-human-biology-bs": "https://humanbiology.stanford.edu/",
    "stanford-symbolic-systems-bs": "https://symsys.stanford.edu/",
    "stanford-mathematics-bs": "https://mathematics.stanford.edu/academics/undergraduate-studies",
    "stanford-political-science-bs": "https://politicalscience.stanford.edu/undergraduate-program",
    "stanford-international-relations-bs": "https://internationalrelations.stanford.edu/",
    "stanford-psychology-bs": "https://psychology.stanford.edu/academics/undergraduate-program",
    "stanford-english-bs": "https://english.stanford.edu/undergraduate",
    "stanford-earth-systems-bs": "https://earth.stanford.edu/earthsys",
    "stanford-energy-science-engineering-ms": "https://ese.stanford.edu/",
    "stanford-mba": "https://www.gsb.stanford.edu/programs/mba",
    "stanford-msx": "https://www.gsb.stanford.edu/programs/msx",
    "stanford-gsb-phd": "https://www.gsb.stanford.edu/programs/phd",
    "stanford-education-ms": "https://ed.stanford.edu/academics/masters",
    "stanford-education-phd": "https://ed.stanford.edu/academics/doctoral",
    "stanford-jd": "https://law.stanford.edu/education/degrees/juris-doctor/",
    "stanford-md": "https://med.stanford.edu/md.html",
}

# ── Who-it's-for + highlights, by degree type (catalog fallbacks) ──────────
_WHO_BY_TYPE = {
    "bachelors": "Undergraduates seeking a rigorous Stanford education with broad research access.",
    "masters": "Graduates seeking advanced, specialized training for technical careers.",
    "phd": "Aspiring scholars pursuing an academic or research career (fully funded).",
    "professional": "Candidates preparing for a licensed profession via an intensive degree.",
}
_HL_BY_TYPE = {
    "bachelors": ["Undergraduate research", "Flexible majors & minors", "Need-blind aid"],
    "masters": ["Specialized coursework", "Silicon Valley proximity", "Industry & research links"],
    "phd": ["Full funding & stipend", "World-class advisors", "Research apprenticeship"],
    "professional": [
        "Clinical / professional training",
        "Interdisciplinary joint degrees",
        "Strong placement",
    ],
}
_WHO_BY_SLUG = {
    "stanford-mba": (
        "Future leaders and entrepreneurs with strong records and a few years of "
        "work experience, seeking a small, transformational general-management program."
    ),
    "stanford-cs-ms": (
        "Technically strong graduates who want to deepen computer-science expertise "
        "in a chosen specialization, often before industry or a PhD."
    ),
}
_HL_BY_SLUG = {
    "stanford-mba": [
        "~424-student class",
        "Finance · Tech · Consulting",
        "Entrepreneurship & VC access",
    ],
    "stanford-cs-ms": ["Ten specializations", "45 units, flexible", "Silicon Valley recruiting"],
}
_WHO_BASELINE = (
    "Students seeking a rigorous Stanford degree with access to world-class research "
    "and Silicon Valley industry connections."
)
_HL_BASELINE = [
    "Private research university",
    "Need-blind undergraduate aid",
    "Silicon Valley proximity",
]
_FOS_CONDITIONS = (
    "Median earnings 1 year after completion for degree recipients in this field of "
    "study, as reported by the U.S. Dept. of Education College Scorecard for Stanford "
    "(UNITID 243744). Not a guarantee of future earnings."
)

# ── Curriculum / tracks, where published ───────────────────────────────────
_TRACKS_BY_SLUG: dict[str, dict] = {
    "stanford-cs-ms": {
        "label": "Specializations",
        "note": (
            "The MS in Computer Science requires 45 units and is completed by "
            "declaring one of ten specializations; students may switch with advisor "
            "approval."
        ),
        "items": [
            {"name": "Artificial Intelligence"},
            {"name": "Biocomputation"},
            {"name": "Computer and Network Security"},
            {"name": "Human-Computer Interaction"},
            {"name": "Information Management and Analytics"},
            {"name": "Real-World Computing"},
            {"name": "Software Theory"},
            {"name": "Systems"},
            {"name": "Theoretical Computer Science"},
            {"name": "Visual Computing"},
        ],
        "source": "Stanford CS — MS specializations",
        "source_url": "https://www.cs.stanford.edu/admissions/masters-admissions",
    },
    "stanford-mba": {
        "label": "Curriculum",
        "note": (
            "A two-year, full-time program: a personalized first-year core "
            "(general management, with placement based on background), then a "
            "largely elective second year drawing on more than 100 electives plus "
            "global experiences and joint/dual degrees."
        ),
        "items": [
            {"name": "First-year general-management core"},
            {"name": "Leadership labs & touchy-feely (Interpersonal Dynamics)"},
            {"name": "Global Experience Requirement"},
            {"name": "100+ second-year electives"},
            {"name": "Joint & dual degrees (MS/CS, MD, JD, MA Education, MPP)"},
        ],
        "source": "Stanford GSB — MBA Academic Experience",
        "source_url": "https://www.gsb.stanford.edu/programs/mba/academic-experience",
    },
}

# ── Program-specific cost (official published rates) ───────────────────────
# Stanford's standard full-time graduate tuition for 2025-26 is $65,910/year
# (College Scorecard, UNITID 243744); the GSB MBA carries its own professional
# rate. PhDs are fully funded. Undergraduate tuition is its own published rate.
_TUITION_UNDERGRAD = 67731  # Stanford full-time undergraduate tuition, 2025-26
_COST_BY_SLUG: dict[str, dict] = {
    "stanford-mba": {
        "tuition_usd": 85755,
        "year": "2025-26",
        "funded": False,
        "breakdown": [
            {"label": "Tuition (9-month academic year)", "amount": 85755},
            {
                "label": "Living, housing, books & personal (estimated, single student)",
                "amount": 50016,
                "note": "Total estimated cost of attendance for a single student is $135,771",
            },
        ],
        "total_cost_of_attendance": 135771,
        "source": "Stanford GSB — Cost of Attendance",
        "source_url": "https://www.gsb.stanford.edu/programs/mba/tuition-financial-aid/cost-attendance",
    },
    "stanford-cs-ms": {
        "tuition_usd": 63540,
        "year": "2025-26",
        "funded": False,
        "note": "Tuition is charged per unit; $21,180 per quarter at 11-18 units (three quarters).",
        "source": "Stanford Student Services — 2025-26 Graduate & Professional Tuition",
        "source_url": "https://studentservices.stanford.edu/tuition-rates/2025-2026-graduate-and-professional-tuition-rates",
    },
}

# ── Program-specific outcomes (the flagship's own employment report) ───────
# Stanford GSB MBA — Class of 2024 Employment Report, quoted verbatim, never
# estimated. Other programs fall back to College Scorecard Field-of-Study medians.
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "stanford-mba": {
        "median_salary": 185000,
        "mean_salary": 187504,
        "median_signing_bonus": 30000,
        "signing_bonus_rate": 0.49,
        "employment_rate": 0.88,
        "employment_timeframe": "received a job offer within three months of graduation",
        "class_size": 432,
        "scope": "program",
        "top_industries": ["Finance (37%)", "Technology (22%)", "Consulting (14%)"],
        "conditions": [
            "Class of 2024 (432 graduates); 249 (58% of the class) were seeking "
            "employment — the rest pursued ventures, sponsored returns, or further study.",
            "88% of job-seekers received an offer and 80% accepted an offer within "
            "three months of graduation.",
            "Median base salary $185,000; mean $187,504. Median signing bonus "
            "$30,000, received by 49% of those reporting.",
            "23% of the class was starting a new venture. Top hiring region: U.S. West (45%).",
        ],
        "source": "Stanford GSB MBA Employment Report, Class of 2024",
        "source_url": "https://www.gsb.stanford.edu/programs/mba/career-impact/employment-outcomes",
    },
}

# College Scorecard Field-of-Study median earnings (1 year after completion) by
# program slug, keyed to the awarded CIP for UNITID 243744. Real, federal, cited.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "stanford-cs-ms": (199761, "11.07"),
    "stanford-cs-bs": (138613, "11.07"),
    "stanford-ee-ms": (159472, "14.10"),
    "stanford-me-ms": (121408, "14.19"),
    "stanford-cee-ms": (83740, "14.08"),
    "stanford-aa-ms": (111760, "14.02"),
    "stanford-economics-bs": (98104, "45.06"),
    "stanford-human-biology-bs": (50179, "30.27"),
    "stanford-symbolic-systems-bs": (105695, "30.25"),
    "stanford-international-relations-bs": (76166, "45.09"),
    "stanford-education-ms": (71967, "13.01"),
}

# Institution-wide outcomes fallback (College Scorecard, UNITID 243744), used for
# degree programs without a published program-level report or FOS earnings.
_OUTCOMES_INSTITUTION = {
    "median_salary": 124080,
    "scope": "institution",
    "note": "Stanford institution-wide median earnings 10 years after entry.",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 243744)",
    "source_url": "https://collegescorecard.ed.gov/school/?243744",
}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "stanford-mba": {
        "cohort_size": "424 students (Class of 2026)",
        "applicants": 7295,
        "international_pct": 0.39,
        "countries": 72,
        "women_pct": 0.44,
        "median_gmat": 738,
        "avg_gpa": 3.75,
        "avg_work_experience_years": 5.1,
        "source": "Stanford GSB — MBA Entering Class Profile (Class of 2026)",
        "source_url": "https://www.gsb.stanford.edu/programs/mba/admission/class-profile",
    },
}

# ── Faculty (lead + directory link), where confidently sourced ─────────────
_FACULTY_BY_SLUG: dict[str, dict] = {
    "stanford-mba": {
        "lead": [
            {"name": "Sarah Soule", "title": "Philip H. Knight Professor and Dean"},
            {"name": "Susan Athey", "title": "Economics of Technology Professor"},
            {
                "name": "Brian Lowery",
                "title": "Walter Kenneth Kilpatrick Professor of Organizational Behavior",
            },
        ],
        "note": "Taught by Stanford Graduate School of Business faculty.",
        "directory_url": "https://www.gsb.stanford.edu/faculty-research/faculty",
    },
    "stanford-cs-ms": {
        "lead": [
            {
                "name": "Mehran Sahami",
                "title": "James and Ellenor Chesebrough Professor; CS chair",
                "url": "https://profiles.stanford.edu/mehran-sahami",
            },
            {
                "name": "Christopher Manning",
                "title": "Thomas M. Siebel Professor in Machine Learning",
            },
        ],
        "note": "Taught by Stanford Computer Science faculty.",
        "directory_url": "https://www.cs.stanford.edu/people/faculty",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources) ────────
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "stanford-mba": {
        "summary": (
            "Students and third-party guides consistently praise the small class "
            "size, the entrepreneurial culture and Silicon Valley access, and the "
            "unusually personal leadership curriculum; the most common cautions are "
            "the extreme selectivity, the high cost of living, and a less "
            "structured recruiting funnel than some East-Coast peers."
        ),
        "themes": [
            {
                "label": "Small, tight-knit class",
                "sentiment": "positive",
                "detail": "About 420 students per class fosters a close, collaborative community.",
            },
            {
                "label": "Entrepreneurship & VC access",
                "sentiment": "positive",
                "detail": "Silicon Valley proximity and a startup-heavy alumni base.",
            },
            {
                "label": "Leadership & self-development",
                "sentiment": "positive",
                "detail": "The 'Interpersonal Dynamics' course and leadership labs are signature.",
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": "Among the lowest MBA admit rates in the world.",
            },
            {
                "label": "High cost of living",
                "sentiment": "caution",
                "detail": "Bay Area housing pushes total cost of attendance above $135K/year.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Stanford GSB",
                "url": "https://poetsandquants.com/2025/06/04/meet-the-stanford-gsb-mba-class-of-2026/",
            },
            {
                "label": "Clear Admit — Stanford GSB",
                "url": "https://www.clearadmit.com/schools/stanford/",
            },
            {
                "label": "BusinessBecause — Stanford MBA jobs & salary",
                "url": "https://www.businessbecause.com/news/mba-jobs-salary/7467/stanford-mba-jobs-salary",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-cs-ms": {
        "summary": (
            "Students and graduate guides consistently rank Stanford's MS in "
            "Computer Science among the world's most selective and prestigious "
            "technical master's programs — QS places Stanford No. 2 globally in "
            "computer science (2026) — praising ten specialization tracks, "
            "Silicon Valley recruiting access, and world-class faculty; common "
            "cautions are that the department offers no financial support for MS "
            "students, admission is extremely competitive, and total cost of "
            "attendance can exceed $125,000 including Bay Area living expenses."
        ),
        "themes": [
            {
                "label": "Global CS standing",
                "sentiment": "positive",
                "detail": (
                    "QS ranks Stanford No. 2 worldwide in computer science (2026), "
                    "behind only MIT."
                ),
            },
            {
                "label": "Flexible specializations",
                "sentiment": "positive",
                "detail": (
                    "The 45-unit MS spans ten tracks from AI and systems to HCI "
                    "and security."
                ),
            },
            {
                "label": "Silicon Valley access",
                "sentiment": "positive",
                "detail": (
                    "Proximity to major tech employers and startup ecosystems is a "
                    "recurring theme in student guides."
                ),
            },
            {
                "label": "No departmental funding",
                "sentiment": "caution",
                "detail": (
                    "Stanford CS does not offer financial support for MS students — "
                    "only U.S. federal loans are available."
                ),
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": (
                    "The MS admits a small fraction of a very large applicant pool "
                    "each year."
                ),
            },
        ],
        "sources": [
            {
                "label": "QS — Computer Science subject rankings (2026)",
                "url": "https://www.topuniversities.com/university-subject-rankings/computer-science-information-systems",
            },
            {
                "label": "Stanford CS — MS admissions FAQ",
                "url": "https://www.cs.stanford.edu/admissions/masters-admissions-frequently-asked-questions",
            },
            {
                "label": "Leland — Stanford MSCS overview",
                "url": "https://www.joinleland.com/library/a/stanford-mscs",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-cs-bs": {
        "summary": (
            "Students and third-party guides consistently rank Stanford "
            "undergraduate computer science among the nation's most popular and "
            "rigorous programs — Niche lists CS as the most common major with "
            "341 graduates in a recent cycle — praising flexible track options, "
            "CURIS summer research, and a coterminal BS/MS pathway; common cautions "
            "are that grading is curved against an exceptionally strong peer group, "
            "introductory courses are large, and the overall admit rate is about 4%."
        ),
        "themes": [
            {
                "label": "Top-tier CS department",
                "sentiment": "positive",
                "detail": (
                    "Stanford CS publishes ten undergraduate tracks and is widely "
                    "cited among the world's leading CS programs."
                ),
            },
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": (
                    "CURIS summer research and honors-thesis pathways give "
                    "undergraduates faculty lab access."
                ),
            },
            {
                "label": "Coterminal MS pathway",
                "sentiment": "positive",
                "detail": (
                    "Students can complete a BS and MS in roughly five years — a "
                    "well-established Stanford pathway."
                ),
            },
            {
                "label": "Curved grading",
                "sentiment": "caution",
                "detail": (
                    "Niche reviewers note that grading on a curve against elite peers "
                    "can feel more demanding than high school."
                ),
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": (
                    "Stanford's undergraduate admit rate is about 4% (Class of 2028)."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford CS — bachelor's program overview",
                "url": "https://www.cs.stanford.edu/academics-overview/academics-bachelors-program",
            },
            {
                "label": "Niche — Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
            {
                "label": "Lantern College Counseling — best CS programs (2026)",
                "url": "https://www.lanterncollegecounseling.com/insights/best-colleges-for-computer-science-how-to-find-the-right-fit-beyond-the-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-jd": {
        "summary": (
            "Students and legal guides rank Stanford Law School No. 1 nationally "
            "for 2026 — the first time it holds the top spot alone after years of "
            "tying Yale — praising a 98.4% full-time employment rate for the Class "
            "of 2024 and a 98.9% ultimate bar-passage rate; common cautions are "
            "extreme selectivity (about 6% acceptance), a demanding workload, and "
            "that California's bar exam is among the nation's more difficult "
            "jurisdictions."
        ),
        "themes": [
            {
                "label": "No. 1 national rank (2026)",
                "sentiment": "positive",
                "detail": (
                    "U.S. News placed Stanford Law alone at No. 1 for 2026, ending "
                    "Yale's long solo reign."
                ),
            },
            {
                "label": "Employment outcomes",
                "sentiment": "positive",
                "detail": (
                    "98.4% of 2024 graduates had full-time, long-term employment "
                    "within ten months."
                ),
            },
            {
                "label": "Bar passage",
                "sentiment": "positive",
                "detail": (
                    "A 98.9% ultimate bar-passage rate (two-year average) in the "
                    "2026 ranking data."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "About 6% acceptance with a median LSAT of 173 and GPA of 3.96."
                ),
            },
            {
                "label": "California bar difficulty",
                "sentiment": "mixed",
                "detail": (
                    "Graduates most often sit for California's bar, which has a "
                    "lower statewide passage rate than many peer states."
                ),
            },
        ],
        "sources": [
            {
                "label": "Bloomberg Law — Stanford Law No. 1 (2026)",
                "url": "https://news.bloomberglaw.com/legal-exchange-insights-and-commentary/stanford-law-knocks-yale-off-1-ranking-for-the-first-time",
            },
            {
                "label": "Tipping the Scales — 2026 U.S. News law rankings",
                "url": "https://tippingthescales.com/rankings/2026-u-s-news-law-school-ranking-stanford-replaces-yale-at-the-top/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-md": {
        "summary": (
            "Students and medical-school guides consistently describe Stanford "
            "School of Medicine as among the nation's most selective and "
            "research-intensive M.D. programs — Shemmassian reports a 5.63% "
            "interview rate and median MCAT of 519 — praising the Discovery "
            "Curriculum, integration with Stanford Health Care, and a small "
            "entering class of about 90 students; common cautions are that "
            "Stanford declined to participate in U.S. News's 2024+ tiered "
            "rankings (listed as unranked), tuition and fees exceed $89,000, and "
            "admissions expect demonstrated research interest alongside clinical "
            "aptitude."
        ),
        "themes": [
            {
                "label": "Research-intensive training",
                "sentiment": "positive",
                "detail": (
                    "The Discovery Curriculum emphasizes scholarship pathways and "
                    "physician-scientist development."
                ),
            },
            {
                "label": "Academic health system",
                "sentiment": "positive",
                "detail": (
                    "Clinical training spans Stanford Health Care and affiliated "
                    "Bay Area hospitals."
                ),
            },
            {
                "label": "Small entering class",
                "sentiment": "positive",
                "detail": (
                    "Roughly 90 students per class supports close faculty mentoring."
                ),
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": (
                    "A sub-6% interview rate and median MCAT of 519 make admission "
                    "highly competitive."
                ),
            },
            {
                "label": "U.S. News unranked",
                "sentiment": "mixed",
                "detail": (
                    "Stanford no longer submits data to U.S. News medical-school "
                    "rankings and appears as unranked in tiered lists."
                ),
            },
        ],
        "sources": [
            {
                "label": "Shemmassian — Medical schools in California (2026)",
                "url": "https://www.shemmassianconsulting.com/blog/medical-schools-in-california",
            },
            {
                "label": "Stanford School of Medicine — M.D. program",
                "url": "https://med.stanford.edu/md.html",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-msx": {
        "summary": (
            "Students and third-party guides describe Stanford's MSx as a "
            "one-year, full-time Master of Science in Management for mid-career "
            "leaders with at least eight years of work experience — Poets&Quants "
            "lists tuition at $143,144 for the 12-month residential program — "
            "praising shared GSB faculty, flexible electives, and full Stanford "
            "GSB alumni status; common cautions are the high tuition plus "
            "opportunity cost of a one-year career break, a smaller cohort than "
            "the two-year MBA, and admissions emphasis on a clear post-program "
            "career plan."
        ),
        "themes": [
            {
                "label": "Mid-career leadership focus",
                "sentiment": "positive",
                "detail": (
                    "Designed for experienced managers — the entering class averages "
                    "roughly 12–14 years of work experience."
                ),
            },
            {
                "label": "GSB ecosystem access",
                "sentiment": "positive",
                "detail": (
                    "MSx students share faculty, electives, and alumni network with "
                    "the two-year MBA."
                ),
            },
            {
                "label": "Entrepreneurship culture",
                "sentiment": "positive",
                "detail": (
                    "BusinessBecause notes a strong startup and executive-placement "
                    "track among MSx graduates."
                ),
            },
            {
                "label": "High total cost",
                "sentiment": "caution",
                "detail": (
                    "One-year tuition near $143,000 plus foregone salary makes total "
                    "cost substantial."
                ),
            },
            {
                "label": "Career-plan scrutiny",
                "sentiment": "caution",
                "detail": (
                    "Admissions weighs whether applicants have a credible "
                    "acceleration, pivot, or entrepreneurial rationale."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Stanford GSB MSx",
                "url": "https://poetsandquants.com/specialized-master/stanford-universitys-graduate-school-of-business-ms-in-management-msx/?pq-directory-type=specialized-master",
            },
            {
                "label": "BusinessBecause — Stanford MSx review",
                "url": "https://www.businessbecause.com/news/reviews/7808/stanford-msx",
            },
            {
                "label": "Stanford GSB — MSx or MBA comparison",
                "url": "https://www.gsb.stanford.edu/programs/msx-or-mba",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-mse-ms": {
        "summary": (
            "Students and graduate guides describe Stanford's MS in Management "
            "Science and Engineering as a quantitative, engineering-based "
            "alternative to an MBA — the department emphasizes optimization, "
            "analytics, and organizational decision-making across seven "
            "specialization tracks including Operations and Analytics — praising "
            "cross-registration with the GSB and d.school and strong placement into "
            "product management, consulting, and tech; common cautions are that "
            "some core MS&E courses are considered less polished than equivalent "
            "GSB offerings and the program is better suited to analytically minded "
            "early-career professionals than to traditional management trainees."
        ),
        "themes": [
            {
                "label": "Quantitative management",
                "sentiment": "positive",
                "detail": (
                    "Combines optimization, probability, and organizational science "
                    "within the School of Engineering."
                ),
            },
            {
                "label": "Track flexibility",
                "sentiment": "positive",
                "detail": (
                    "Seven specialties span financial analytics, health systems, "
                    "and computational social science."
                ),
            },
            {
                "label": "Cross-campus access",
                "sentiment": "positive",
                "detail": (
                    "Students routinely take electives at the GSB, d.school, and "
                    "peer engineering departments."
                ),
            },
            {
                "label": "PM & tech placement",
                "sentiment": "positive",
                "detail": (
                    "Product management, consulting, and Silicon Valley tech are "
                    "the canonical career paths."
                ),
            },
            {
                "label": "Not a substitute MBA",
                "sentiment": "mixed",
                "detail": (
                    "Student guides note MS&E is more technical and less "
                    "network-driven than a two-year MBA."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford MS&E — MS program overview",
                "url": "https://msande.stanford.edu/ms-program",
            },
            {
                "label": "Stanford MS&E — MS admission requirements",
                "url": "https://msande.stanford.edu/academics-admissions/graduate/admission/ms-admission",
            },
            {
                "label": "Medium — MS&E student perspective",
                "url": "https://medium.com/@giancarlo_benedetti/ms-e-the-cheaper-mba-de358eaeac20",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-ee-ms": {
        "summary": (
            "Students and graduate guides rank Stanford Electrical Engineering "
            "among the world's leading EE departments — Times Higher Education "
            "places Stanford No. 6 globally (2025) with engineering among its "
            "core strengths — praising depth in integrated circuits, photonics, "
            "and information systems plus Silicon Valley hardware recruiting; "
            "common cautions are that the MS is coursework- or research-oriented "
            "without guaranteed departmental funding, admission is highly "
            "selective, and Bay Area living costs are high."
        ),
        "themes": [
            {
                "label": "World-class EE research",
                "sentiment": "positive",
                "detail": (
                    "Faculty strength spans hardware, signals, photonics, and "
                    "computing systems."
                ),
            },
            {
                "label": "Silicon Valley hardware ties",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into semiconductor, systems, and deep-tech "
                    "employers across the Bay Area."
                ),
            },
            {
                "label": "Flexible MS paths",
                "sentiment": "positive",
                "detail": (
                    "The 45-unit MS can be structured around coursework or a "
                    "research thesis."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Graduate admission to Stanford engineering programs is "
                    "highly competitive."
                ),
            },
            {
                "label": "Cost of living",
                "sentiment": "caution",
                "detail": (
                    "Bay Area housing pushes total graduate cost well above tuition "
                    "alone."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford EE — graduate admissions",
                "url": "https://ee.stanford.edu/academics/graduate-admissions",
            },
            {
                "label": "Times Higher Education — Stanford University (2025)",
                "url": "https://www.timeshighereducation.com/world-university-rankings/stanford-university",
            },
            {
                "label": "Niche — Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-me-bs": {
        "summary": (
            "Students and third-party guides describe Stanford's undergraduate "
            "mechanical engineering as a rigorous SoE major emphasizing design, "
            "robotics, thermosciences, and biomechanics — the SoE undergraduate "
            "handbook highlights extensive lab and project coursework — praising "
            "small-group design sequences and access to the Product Realization Lab; "
            "common cautions are a demanding core alongside Stanford's humanities "
            "requirements, large lower-division math and physics courses, and that "
            "students must proactively seek research mentors."
        ),
        "themes": [
            {
                "label": "Design & robotics depth",
                "sentiment": "positive",
                "detail": (
                    "ME at Stanford emphasizes hands-on design, mechanics, and "
                    "thermosciences."
                ),
            },
            {
                "label": "Product Realization Lab",
                "sentiment": "positive",
                "detail": (
                    "The PRL gives undergraduates machine-shop and prototyping "
                    "access rare among peer programs."
                ),
            },
            {
                "label": "Research pathways",
                "sentiment": "positive",
                "detail": (
                    "SoE summer research programs connect undergraduates to "
                    "faculty labs."
                ),
            },
            {
                "label": "Heavy core workload",
                "sentiment": "caution",
                "detail": (
                    "Engineering fundamentals plus Stanford's breadth requirements "
                    "create a packed schedule."
                ),
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": (
                    "Lower-division math and physics sections can be large before "
                    "students reach ME depth courses."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford SoE — Mechanical Engineering program",
                "url": "https://ughb.stanford.edu/majors-minors/mechanical-engineering-program",
            },
            {
                "label": "Stanford ME — undergraduate program",
                "url": "https://me.stanford.edu/academics-admissions/undergraduate-program",
            },
            {
                "label": "Niche — Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-economics-bs": {
        "summary": (
            "Students and third-party guides rank Stanford's undergraduate "
            "economics among the nation's strongest — the department sits in the "
            "School of Humanities and Sciences with ties to SIEPR and the GSB — "
            "praising rigorous micro, macro, and econometrics training and a path "
            "into finance, consulting, and PhD programs; common cautions are large "
            "lecture sections in popular courses, a competitive curve, and that "
            "students seeking a pre-professional business degree often cross-register "
            "at the GSB rather than majoring in economics alone."
        ),
        "themes": [
            {
                "label": "Rigorous quantitative training",
                "sentiment": "positive",
                "detail": (
                    "The major stresses micro theory, econometrics, and mathematical "
                    "modeling."
                ),
            },
            {
                "label": "Research institute ties",
                "sentiment": "positive",
                "detail": (
                    "SIEPR and GSB faculty connections give undergraduates exposure "
                    "to policy and finance research."
                ),
            },
            {
                "label": "Career versatility",
                "sentiment": "positive",
                "detail": (
                    "Graduates pursue consulting, finance, tech, policy, and "
                    "economics PhD programs."
                ),
            },
            {
                "label": "Large lectures",
                "sentiment": "caution",
                "detail": (
                    "Popular intermediate courses can enroll hundreds of students."
                ),
            },
            {
                "label": "Not a business major",
                "sentiment": "mixed",
                "detail": (
                    "Stanford has no undergraduate business school; economics is the "
                    "closest quantitative social-science option."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford Economics — undergraduate program",
                "url": "https://economics.stanford.edu/academics/undergraduate-program",
            },
            {
                "label": "Niche — Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
            {
                "label": "Stanford SIEPR — research overview",
                "url": "https://siepr.stanford.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-symbolic-systems-bs": {
        "summary": (
            "Students and third-party guides describe Stanford's Symbolic Systems "
            "major as a signature interdisciplinary program blending computer "
            "science, linguistics, philosophy, psychology, and statistics — "
            "IvyWise ranks it among Stanford's most popular and most unique majors "
            "— praising its focus on human and machine intelligence and strong "
            "placement into product management and software engineering; common "
            "cautions are that the concentration is unique to Stanford (less "
            "recognized off-campus than CS alone), advising can feel fragmented "
            "across departments, and the curriculum demands breadth across both "
            "humanities and technical fields."
        ),
        "themes": [
            {
                "label": "Signature Stanford major",
                "sentiment": "positive",
                "detail": (
                    "SymSys is widely cited as one of Stanford's most distinctive "
                    "undergraduate programs."
                ),
            },
            {
                "label": "Human + machine intelligence",
                "sentiment": "positive",
                "detail": (
                    "Coursework spans cognitive science, AI, linguistics, and "
                    "philosophy of mind."
                ),
            },
            {
                "label": "Tech career paths",
                "sentiment": "positive",
                "detail": (
                    "Alumni frequently enter product management, software "
                    "engineering, and research."
                ),
            },
            {
                "label": "Interdisciplinary complexity",
                "sentiment": "mixed",
                "detail": (
                    "Students navigate requirements across multiple departments with "
                    "varying advising styles."
                ),
            },
            {
                "label": "Less portable label",
                "sentiment": "caution",
                "detail": (
                    "Employers off-campus may be less familiar with 'Symbolic "
                    "Systems' than a straight CS degree."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford Symbolic Systems Program",
                "url": "https://symsys.stanford.edu/",
            },
            {
                "label": "Stanford Bulletin — SYMBO-BS",
                "url": "https://bulletin.stanford.edu/programs/SYMBO-BS",
            },
            {
                "label": "IvyWise — top Stanford majors",
                "url": "https://www.ivywise.com/blog/top-10-most-popular-majors-at-stanford/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-human-biology-bs": {
        "summary": (
            "Students and third-party guides describe Stanford Human Biology as "
            "one of the university's most popular pre-health majors — Niche lists "
            "biology among the top three majors by graduates — praising "
            "interdisciplinary study of human health, behavior, and policy plus "
            "access to Stanford Medicine research; common cautions are that the "
            "major is competitive to declare, pre-med course sequencing is "
            "demanding alongside HumBio breadth requirements, and pre-health "
            "advising can feel crowded given the large applicant pool."
        ),
        "themes": [
            {
                "label": "Popular pre-health path",
                "sentiment": "positive",
                "detail": (
                    "Human Biology is a leading route for Stanford students pursuing "
                    "medicine and health careers."
                ),
            },
            {
                "label": "Interdisciplinary health focus",
                "sentiment": "positive",
                "detail": (
                    "The major integrates biology, epidemiology, and health policy "
                    "rather than a narrow molecular track."
                ),
            },
            {
                "label": "Medical campus access",
                "sentiment": "positive",
                "detail": (
                    "Proximity to Stanford Medicine supports research and clinical "
                    "shadowing opportunities."
                ),
            },
            {
                "label": "Crowded pre-med pipeline",
                "sentiment": "caution",
                "detail": (
                    "A large share of undergraduates pursue medicine, intensifying "
                    "competition for research and advising."
                ),
            },
            {
                "label": "Heavy course load",
                "sentiment": "caution",
                "detail": (
                    "Pre-med prerequisites plus HumBio core courses create a packed "
                    "schedule."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford Human Biology Program",
                "url": "https://humbio.stanford.edu/",
            },
            {
                "label": "Niche — Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
            {
                "label": "Stanford Bulletin — HUMBIO-BS",
                "url": "https://bulletin.stanford.edu/programs/HUMBIO-BS",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "stanford-bioe-bs": {
        "summary": (
            "Students and third-party guides describe Stanford's undergraduate "
            "bioengineering as a School of Engineering major at the interface of "
            "biology and medicine — the SoE handbook emphasizes quantitative "
            "life-science training with lab and design components — praising "
            "access to Bio-X and translational research on campus; common cautions "
            "are that the major requires strong math and chemistry preparation, "
            "competition for faculty-lab spots is intense, and the program is "
            "smaller than CS or HumBio with fewer built-in peer cohorts."
        ),
        "themes": [
            {
                "label": "Biology-meets-engineering",
                "sentiment": "positive",
                "detail": (
                    "BioE trains students at the intersection of molecular biology "
                    "and engineering design."
                ),
            },
            {
                "label": "Bio-X research ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Campus institutes connect undergraduates to biomedical "
                    "engineering research."
                ),
            },
            {
                "label": "Pre-med & industry paths",
                "sentiment": "positive",
                "detail": (
                    "Graduates pursue medicine, biotech, and graduate bioengineering "
                    "programs."
                ),
            },
            {
                "label": "Quantitative prerequisites",
                "sentiment": "caution",
                "detail": (
                    "Strong calculus, chemistry, and physics are required before "
                    "upper-division BioE courses."
                ),
            },
            {
                "label": "Smaller cohort",
                "sentiment": "caution",
                "detail": (
                    "Fewer majors than CS or HumBio means students build community "
                    "more proactively."
                ),
            },
        ],
        "sources": [
            {
                "label": "Stanford Bioengineering — undergraduate program",
                "url": "https://bioengineering.stanford.edu/academics-admissions/undergraduate-program",
            },
            {
                "label": "Stanford SoE — Bioengineering program sheet",
                "url": "https://ughb.stanford.edu/majors-minors/bioengineering-program",
            },
            {
                "label": "Niche — Stanford University",
                "url": "https://www.niche.com/colleges/stanford-university/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
}

# ── Application requirements (degree-type baselines) ────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or Coalition Application", "required": True},
        {"name": "Stanford questions & short essays", "required": True},
        {"name": "School report + counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "Official transcript", "required": True},
        {
            "name": "SAT or ACT scores",
            "required": True,
            "note": "Stanford requires SAT/ACT again this cycle — verify on the official page.",
        },
        {"name": "$90 application fee or fee waiver", "required": True},
    ],
    "deadlines": [
        {"round": "Restrictive Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 5"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL"],
            "required": False,
            "note": "No separate English test required; TOEFL recommended for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Stanford Undergraduate Admission", "url": "https://admission.stanford.edu/"}
        ],
    },
    "source": "Stanford Undergraduate Admission",
    "source_url": "https://admission.stanford.edu/apply/first-year/",
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
            "note": "Many departments are GRE-optional or don't consider it — check first.",
        },
        {
            "name": "TOEFL for international applicants",
            "required": False,
            "note": "Required if your first language is not English; waivers available.",
        },
    ],
    "recommendations": {
        "required_count": 3,
        "types": ["Three academic or professional letters of recommendation"],
    },
    "deadlines": [
        {
            "round": "Department deadlines (typically December)",
            "date": "Varies by department — verify on the program page",
        }
    ],
    "international": {
        "english": {
            "tests": ["TOEFL"],
            "required": True,
            "note": "Minimum TOEFL iBT 100 recommended; waived for degrees earned in English.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Stanford Graduate Admissions", "url": "https://gradadmissions.stanford.edu/"}
        ],
    },
    "source": "Stanford Graduate Admissions",
    "source_url": "https://gradadmissions.stanford.edu/",
}
_REQ_PROFESSIONAL = {
    "materials": [
        {"name": "Online application (LSAC/AMCAS as applicable)", "required": True},
        {"name": "Personal statement & essays", "required": True},
        {"name": "Letters of recommendation", "required": True},
        {"name": "Transcripts", "required": True},
        {"name": "Admission test (LSAT/GRE for JD; MCAT for MD)", "required": True},
    ],
    "deadlines": [
        {"round": "Annual cycle", "date": "Varies by school — verify on the program page"}
    ],
    "international": {
        "visa": _INTL_VISA,
        "sources": [
            {"label": "Stanford Graduate Admissions", "url": "https://gradadmissions.stanford.edu/"}
        ],
    },
    "source": "Stanford professional-school admissions",
    "source_url": "https://www.stanford.edu/admission/",
}
_REQ_MBA = {
    "materials": [
        {"name": "Stanford GSB online application", "required": True},
        {"name": "Two essays (incl. 'What matters most to you, and why?')", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Two letters of reference", "required": True},
        {"name": "Résumé", "required": True},
        {
            "name": "GMAT or GRE",
            "required": True,
            "note": "Either test is accepted; no minimum score.",
        },
        {"name": "$275 application fee", "required": False},
    ],
    "recommendations": {
        "required_count": 2,
        "types": ["Two professional letters of reference (a current supervisor is recommended)"],
    },
    "deadlines": [
        {"round": "Round 1", "date": "Mid-September"},
        {"round": "Round 2", "date": "Early January"},
        {"round": "Round 3", "date": "Mid-April"},
    ],
    "test_policy": {
        "stance": "required",
        "accepted_tests": ["GMAT", "GRE"],
        "note": "GMAT or GRE required; either is accepted with no minimum.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": False,
            "note": "English-proficiency proof can strengthen an application; not required of all.",
        },
        "visa": _INTL_VISA,
        "opt": "MBA students are eligible for OPT; consult the Bechtel International Center.",
        "sources": [
            {
                "label": "Stanford GSB MBA — Application",
                "url": "https://www.gsb.stanford.edu/programs/mba/admission",
            }
        ],
    },
    "source": "Stanford GSB MBA Admission",
    "source_url": "https://www.gsb.stanford.edu/programs/mba/admission",
}


# Main Quad leads the institution hero; see ``SCHOOL_OUTCOMES["campus_photos"]``.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Stanford to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Stanford is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1885
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.stanford.edu"
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
        # GSB carries its own Insights RSS; every other school filters Stanford Report.
        sc.content_sources = _GSB_CONTENT if spec["name"] == _GSB else _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this is
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


def _program_standard(
    slug: str, spec: dict | None = None, has_program_outcomes: bool = False
) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    if spec is None:
        spec = _SPEC_BY_SLUG[slug]
    omitted: list[str] = []
    if slug != _FLAGSHIP:
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    if not has_program_outcomes and slug != _FLAGSHIP:
        omitted.append("outcomes_data.conditions")
    if spec["degree_type"] not in ("bachelors",) and slug not in _COST_BY_SLUG:
        omitted.append("cost_data.tuition_usd")
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    explicit_req_slugs = {_FLAGSHIP, "stanford-jd", "stanford-md"}
    if slug not in explicit_req_slugs and spec["degree_type"] != "bachelors":
        omitted.append("application_requirements.deadlines")
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
        p.department = spec.get("department")
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        if slug == _FLAGSHIP:
            p.content_sources = _MBA_CONTENT
        else:
            p.content_sources = _program_content(spec)
        # Cost: program override (official) → funded PhD → undergrad rate →
        # professional (omitted, varies) → standard grad rate.
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0,
                "funded": True,
                "note": "PhD students receive full tuition plus a stipend.",
                "source": "Stanford Graduate Admissions",
                "source_url": "https://gradadmissions.stanford.edu/",
                "year": "2025-26",
            }
        elif spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UNDERGRAD
            p.cost_data = {
                "tuition_usd": _TUITION_UNDERGRAD,
                "funded": False,
                "source": "Stanford Student Services — 2025-26 Undergraduate Tuition",
                "source_url": "https://studentservices.stanford.edu/tuition-rates/2025-2026-undergraduate-tuition-rates",
                "year": "2025-26",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": spec["degree_type"] == "phd",
                "note": (
                    "Stanford does not publish a single citable per-program tuition for this "
                    "catalog node; see the program's official admissions/tuition page."
                ),
                "source": "Stanford Graduate Admissions",
                "source_url": "https://gradadmissions.stanford.edu/",
            }
        # Admissions: program override → MBA → professional → undergrad → grad.
        if slug == "stanford-mba":
            p.application_requirements = dict(_REQ_MBA)
        elif spec["degree_type"] == "professional":
            p.application_requirements = dict(_REQ_PROFESSIONAL)
        elif spec["degree_type"] == "bachelors":
            p.application_requirements = dict(_REQ_UNDERGRAD)
        else:
            p.application_requirements = dict(_REQ_GRAD)
        # Outcomes precedence: program report → Scorecard FOS → institution median.
        out_override = _OUTCOMES_BY_SLUG.get(slug)
        fos = _FOS_OUTCOMES.get(slug)
        if out_override is not None:
            outcomes = dict(out_override)
            has_program_outcomes = True
        elif fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "conditions": _FOS_CONDITIONS,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?243744",
            }
            has_program_outcomes = True
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
            has_program_outcomes = False
        outcomes["_standard"] = _program_standard(slug, spec, has_program_outcomes)
        p.outcomes_data = outcomes
        p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
        p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming cycle).
        if slug == "stanford-mba":
            p.application_deadline = date(2027, 1, 7)
        elif spec["degree_type"] == "bachelors":
            p.application_deadline = date(2027, 1, 5)
        else:
            p.application_deadline = date(2026, 12, 1)
    session.flush()
    # Reconcile legacy Stanford programs (slug not in the canonical set): delete
    # when unreferenced, otherwise unpublish so the catalog stays clean without
    # breaking any application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
