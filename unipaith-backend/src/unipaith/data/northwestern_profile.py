"""Northwestern University — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Sloan / MBAn reference instance (see ``mit_profile.py`` /
``jhu_profile.py``): every value is researched from an authoritative source and
carries a citation, or is honestly omitted (recorded in that node's ``_standard.omitted``)
— never guessed. Built 2026-06-13 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 147767):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    endowment, undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **Northwestern Common Data Set 2024-2025** and the Office of Institutional Research:
    the Fall 2024 first-year admissions funnel, total enrollment, and the 6:1
    student-faculty ratio; Class of 2029 funnel (53,284 applicants / 3,710 admits)
    from The Daily Northwestern (April 2025).
  * Rankings: **U.S. News Best Colleges 2026** (#7 National), **QS 2026** (#42),
    **Times Higher Education 2026** (#30), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official **Northwestern Academics** schools-and-colleges index plus
    the College Scorecard Field-of-Study catalog (306 CIP rows) mapped to Northwestern's
    eleven U.S. main-campus schools (Qatar excluded). School of Professional Studies
    programs carry ``delivery_format = "online"`` where applicable per IPEDS.
  * Northwestern leadership pages and school websites for each unit's dean, and a
    verified 5-photo Wikimedia Commons campus gallery (author + license confirmed
    via the Commons API).
  * Verified third-party coverage + official rankings for coverable programs.

Honest caveats stamped into ``_standard.omitted``: Northwestern does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted.

Graduate-tier tuition repair (2026-06-22, nwtuition1): stamps each master's /
professional row from its owning school's published 2025-26 Northwestern Student
Financial Services rate (quarterly / trimester / semester / per-unit totals converted
to the annual or program-total figure the matcher reads), every value DISTINCT from
the $68,322 undergraduate sticker — never the undergrad number copied down.
Funded research doctorates carry ``tuition_usd = 0`` with a funded note (TGS policy).

Catalog repair (2026-06-16, northwesternprof3): de-fabricates the IPEDS breadth catalog —
maps CIP rollup titles to real Northwestern degree names and owning departments, and
re-stamps every node at ``STANDARD_VERSION`` 2.

Description depth pass (2026-06-16, northwesternprof4): replaces all classification-only
program descriptions with field-specific clauses from ``northwestern_field_descriptions.py``.

Description repair (2026-06-17, northwesternprof5): drops ``{program_name}:`` prefix from
all descriptions (gold MIT/JHU pattern); fixes peer-institution contamination in field
clauses (Chesapeake, Writing Seminars, Bloomberg, etc.); 0% name-prefixed descriptions.

Description repair (2026-06-20, nwdefab1): replaces suffix-diversifier stamping with
per-credential description leads so BA/MS/PhD siblings no longer share a ≥120-char
leading body (REPAIR BACKLOG #6 — gold MIT = 0% shared-leading-body; anti-stub clean).

De-fabrication (2026-06-18, northwesternprof7): REMOVES the ``DEPTH_REVIEWS`` batch (48
machine-synthesized external_reviews minted one-per-row from program metadata + institution
rankings — repeated institution-level themes across 11–15 programs, 37 rows citing a bare
"U.S. News — Northwestern University" source, several attached to CIP-rollup rows). A review
fabricated-by-synthesis lends a row false third-party credibility and is worse than an
honest blank (SKILL.md miss #8), so those programs now record ``external_reviews`` in
``_standard.omitted``; only the hand-gathered, program-specific flagship reviews remain
(``_REVIEWS_BY_SLUG``). Also repairs the last peer-copied field clause (Operations Research
named Berkeley's "IEOR … Haas … CDSS"; now Northwestern's real IEMS department + Center for
Optimization and Statistical Learning). An enforced anti-synthesis test
(``tests/test_northwestern_profile.py``) blocks any future one-sweep review mint.

FULL CATALOG REBUILD (2026-06-20, nwrebuild1): the prior catalog was an IPEDS×award-level
mint — 306 CIP rows renamed by alias maps, described by a FIELD-keyed shared body with a
per-credential frame prepended (so a field's BA/MS/PhD shared one body in the tail), and
that shared body was PERVASIVELY peer-contaminated (Kellogg renamed "Northwestern Business
School … world's first collegiate business school" = Wharton; "Sibley School" = Cornell;
"Rausser/CALS/land-grant/New York State" = Berkeley/Cornell; "Weill Northwestern … New York
City" = Weill Cornell; "Longwood Medical Area" = Harvard; "Peabody Conservatory … Mount
Vernon campus" = Johns Hopkins; "Applied Physics Laboratory" = JHU; "Lawrence Northwestern"
= Berkeley/Livermore), and it minted programs Northwestern does not offer (agriculture,
animal science, dental medicine, veterinary). This rebuild REPLACES the entire mint with an
EXPLICIT, researched catalog of Northwestern's REAL degree programs — every name, owning
department, school, and a per-credential field-specific description grounded ONLY in verified
Northwestern units. Sources: the official Northwestern undergraduate catalog
(catalogs.northwestern.edu), the university Graduate Degree Programs A-Z
(northwestern.edu/academics/graduate-a-to-z.html), and each school's pages. The three
contaminated helper modules (northwestern_field_descriptions / northwestern_catalog_maps /
northwestern_ipeds_catalog) are no longer imported. Catalog is de-padded to Northwestern's
real published programs (REPAIR BACKLOG #1 cross-institution contamination + #6
frame+tail-share); gold MIT = 0% on every anti-stub metric.

Matcher-core enrichment (2026-06-26, nwcipwho1): stamps the verified IPEDS CIP family
``cip_code`` on every program (the CPEF field-signal join key — was null catalog-wide,
REPAIR_BACKLOG #1) and fills a PROGRAM-DISTINCT ``who_its_for`` on every program
(distinct/total = 1.0 — 12 hand-written flagship statements + a field-interpolated,
credential-aware frame for the rest; was empty catalog-wide, REPAIR_BACKLOG #4) — never a
degree-type template, never ``= None``. Build gates assert cip coverage + format and
who_its_for coverage + distinctness ≥ 0.9. Tuition was already verified per-tier (71
bachelor's / 26 master's / 4 professional priced, 24 PhD funded $0); descriptions / names /
departments / feeds / campus gallery / flagship reviews unchanged (already gold-clean).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze as _anti_stub_analyze
from unipaith.profile_standard.anti_stub import machine_artifacts as _machine_artifacts

INSTITUTION_NAME = "Northwestern University"
ENRICHED_AT = "2026-06-26"

# Peer-institution signature strings that must NEVER appear in a Northwestern description
# (the run-65 cross-institution contamination class). Each description is researched from
# Northwestern's OWN pages and references only verified Northwestern units, so the import-time
# gate below asserts zero hits.
_PEER_SIGNATURES: tuple[str, ...] = (
    "Peabody",
    "Mount Vernon",
    "Lawrence Northwestern",
    "Applied Physics Laboratory",
    "world's first collegiate",
    "land-grant",
    "Rausser",
    "CALS",
    "Chesapeake",
    "Weill ",
    "Wharton",
    " SAS ",
    "Sibley School",
    "Longwood Medical",
    "Finger Lakes",
    "Writing Seminars",
    "Graduate School of Design",
    "Faculty of Arts & Sciences",
    "Northwestern Business School",
    "Northwestern Faculty",
    "Northwestern Kellogg Law",
    "Northwesternsylvania",
    "Kelly Writers House",
    "Bloomberg health",
    "Bloomberg mental",
    "Bloomberg medical",
    "McCormick and Bloomberg",
)

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CRED_PREFIX_RE = re.compile(
    r"^(Bachelor's|Master's|Professional program) in ",
)
_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate major|a graduate degree|a doctoral program|"
    r"a graduate certificate|a professional degree|a degree program) at ",
)


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 42,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/northwestern-university",
    },
    "times_higher_education": {
        "rank": 30,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/northwestern-university",
    },
    "us_news_national": {
        "rank": 7,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.074,
    "avg_net_price": 29167,
    "median_earnings_10yr": 89363,
    "completion_rate_4yr_150pct": 0.9551,
    "retention_rate_first_year": 0.981,
    "graduation_rate_6yr": 0.9551,
    "financial_aid": {
        "pell_grant_rate": 0.1855,
        "federal_loan_rate": 0.1708,
        "cost_of_attendance": 91250,
        "median_debt_completers": 15000,
        "avg_net_price": 29167,
    },
    "demographics": {
        "white": 0.30,
        "asian": 0.21,
        "hispanic": 0.16,
        "black": 0.08,
        "two_or_more": 0.08,
        "international": 0.12,
        "unknown": 0.04,
    },
    "test_scores": {
        "sat_reading_25_75": [740, 770],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    "campus_basics": {"location": "Evanston, Illinois"},
    "scale": {
        "campus_acres": 240,
        "endowment_usd": 15300000000,
        "student_faculty_ratio": "6:1",
        "faculty_count": 3300,
    },
    "location": {"lat": 42.0565, "lng": -87.6753},
    "research": {
        "areas": [
            "Nanotechnology",
            "Sustainability and energy",
            "Clinical and translational sciences",
            "Social policy research",
            "Bioelectronics",
            "Complex systems and network science",
        ],
        "labs": [
            "International Institute for Nanotechnology",
            "Institute for Policy Research",
            "Paula M. Trienens Institute for Sustainability and Energy",
            "Querrey Simpson Institute for Bioelectronics",
            "Northwestern Institute on Complex Systems",
            "Chemistry of Life Processes Institute",
            "Robert H. Lurie Comprehensive Cancer Center",
            "Northwestern University Clinical and Translational Sciences (NUCATS) Institute",
            "Buffett Institute for Global Affairs",
        ],
        "lab_links": {
            "International Institute for Nanotechnology": "https://www.iinano.org/",
            "Institute for Policy Research": "https://www.ipr.northwestern.edu/",
            "Paula M. Trienens Institute for Sustainability and Energy": "https://trienens-institute.northwestern.edu/",
            "Querrey Simpson Institute for Bioelectronics": "https://bioelectronics.northwestern.edu/",
            "Northwestern Institute on Complex Systems": "https://www.nico.northwestern.edu/",
            "Chemistry of Life Processes Institute": "https://clp.northwestern.edu/",
            "Robert H. Lurie Comprehensive Cancer Center": "https://www.cancer.northwestern.edu/",
            "Northwestern University Clinical and Translational Sciences (NUCATS) Institute": "https://www.nucats.northwestern.edu/",
            "Buffett Institute for Global Affairs": "https://buffett.northwestern.edu/",
        },
    },
    "campus_life": {
        "student_orgs": 500,
        "varsity_sports": 19,
        "athletics_division": "NCAA Division I (Big Ten)",
        "resources": [
            {"name": "Northwestern Athletics", "url": "https://nusports.com/"},
            {
                "name": "Student Organizations & Activities",
                "url": "https://www.northwestern.edu/studentorgs/",
            },
            {
                "name": "Norris University Center",
                "url": "https://www.northwestern.edu/norris/",
            },
            {"name": "Residential Services", "url": "https://www.northwestern.edu/living/"},
            {
                "name": "Campus Experience",
                "url": "https://www.northwestern.edu/campus-experience/",
            },
        ],
    },
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Deering_front.jpg/1920px-Deering_front.jpg",
            "credit": "Wikimedia Commons / Madcoverboy (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Aerial_view_of_Northwestern_University.png/1920px-Aerial_view_of_Northwestern_University.png",
            "credit": "Wikimedia Commons / Sakuav (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Entrance_to_Northwestern_University_Technological_Institute_%2851725404073%29.jpg/1920px-Entrance_to_Northwestern_University_Technological_Institute_%2851725404073%29.jpg",
            "credit": "Wikimedia Commons / Chris Rycroft (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Frances_Searle_Building.jpg/1920px-Frances_Searle_Building.jpg",
            "credit": "Wikimedia Commons / Smandlso (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Ford_Motor_Company_Design_Center%2C_Northwestern_University_%283404284231%29.jpg/1920px-Ford_Motor_Company_Design_Center%2C_Northwestern_University_%283404284231%29.jpg",
            "credit": "Wikimedia Commons / Clara S. (CC BY 2.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Madcoverboy (CC BY-SA 3.0)",
    "flagship": {
        "applicants": 53284,
        "admits": 3710,
        "admissions_cycle": "First-year, Class of 2029 (The Daily Northwestern, April 2025)",
        "founded_year": 1851,
    },
    "sources": [
        {
            "label": "College Scorecard (UNITID 147767)",
            "url": "https://collegescorecard.ed.gov/school/?147767-Northwestern-University",
        },
        {
            "label": "Northwestern Office of Institutional Research — Common Data Set",
            "url": "https://enrollment.northwestern.edu/data/",
        },
        {
            "label": "U.S. News — Northwestern University",
            "url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
        },
    ],
}

UNDERGRAD_COUNT = 9000

DESCRIPTION = (
    "Northwestern University is a private research university in Evanston, IL, founded "
    "in 1851 on the shore of Lake Michigan just north of Chicago. A founding member of "
    "the Big Ten Conference, it pairs a 240-acre lakefront campus and a 6:1 student-faculty "
    "ratio with a research enterprise that draws more than $1 billion in annual funding. "
    "Its International Institute for Nanotechnology, established in 2000, was the first "
    "institute of its kind in the United States.\n\n"
    "Northwestern is organized into eleven degree-granting schools on its U.S. main campus "
    "— Weinberg College of Arts and Sciences, McCormick School of Engineering and Applied "
    "Science, Medill School of Journalism, Media, Integrated Marketing Communications, "
    "the School of Communication, Bienen School of Music, School of Education and Social "
    "Policy, Kellogg School of Management, Pritzker School of Law, Feinberg School of "
    "Medicine, The Graduate School, and the School of Professional Studies — offering "
    "hundreds of programs across the bachelor's, master's, professional, and doctoral levels.\n\n"
    "A Carnegie R1 university accredited by the Higher Learning Commission, Northwestern "
    "ranks #7 among national universities by U.S. News, #30 in the world by Times Higher "
    "Education, and #42 by QS for 2026. Its research footprint runs from the International "
    "Institute for Nanotechnology and the Querrey Simpson Institute for Bioelectronics to "
    "the Robert H. Lurie Comprehensive Cancer Center and the Buffett Institute for Global "
    "Affairs.\n\n"
    "Northwestern's published cost of attendance is about $91,250 a year, but its average "
    "net price after grant aid is about $29,167 and the median federal debt of completers "
    "is about $15,000. Northwestern graduates earn a median of roughly $89,363 ten years "
    "after entry. The Wildcats compete in NCAA Division I as a member of the Big Ten "
    "Conference."
)

# ── School constants ───────────────────────────────────────────────────────

WEINBERG = "Weinberg College of Arts and Sciences"
MCCORMICK = "McCormick School of Engineering and Applied Science"
MEDILL = "Medill School of Journalism, Media, Integrated Marketing Communications"
COMMUNICATION = "School of Communication"
BIENEN = "Bienen School of Music"
SESP = "School of Education and Social Policy"
KELLOGG = "Kellogg School of Management"
LAW = "Pritzker School of Law"
FEINBERG = "Feinberg School of Medicine"
TGS = "The Graduate School"
SPS = "School of Professional Studies"

_SCHOOL_META = [
    {
        "name": WEINBERG,
        "sort_order": 1,
        "website": "https://weinberg.northwestern.edu/",
        "leadership": "Adrian Randolph — Dean",
        "research_centers": [
            "Department of Economics",
            "Department of Psychology",
            "Department of Physics and Astronomy",
            "Institute for Policy Research",
            "Center for Applied Quantum Information",
        ],
        "keywords": ["Weinberg College", "Arts and Sciences", "undergraduate"],
    },
    {
        "name": MCCORMICK,
        "sort_order": 2,
        "website": "https://www.mccormick.northwestern.edu/",
        "leadership": "Christopher Schuh — Dean",
        "research_centers": [
            "Segal Design Institute",
            "Center for Engineering and Health",
            "Northwestern Institute on Complex Systems (NICO)",
            "Center for Interdisciplinary Exploration and Research in Astrophysics (CIERA)",
            "International Institute for Nanotechnology",
        ],
        "keywords": ["McCormick School", "engineering", "biomedical engineering"],
    },
    {
        "name": MEDILL,
        "sort_order": 3,
        "website": "https://www.medill.northwestern.edu/",
        "leadership": "Charles Whitaker — Dean",
        "research_centers": [
            "Knight Lab",
            "Local News Initiative",
            "Medill IMC Center",
            "Washington Program",
        ],
        "keywords": ["Medill", "journalism", "IMC", "media"],
    },
    {
        "name": COMMUNICATION,
        "sort_order": 4,
        "website": "https://communication.northwestern.edu/",
        "leadership": "E. Patrick Johnson — Dean",
        "research_centers": [
            "Center for Communication and Health",
            "Center for Communication Studies",
            "School of Communication Theatre Program",
            "Performance Studies",
        ],
        "keywords": ["School of Communication", "theatre", "RTVF", "performance studies"],
    },
    {
        "name": BIENEN,
        "sort_order": 5,
        "website": "https://www.music.northwestern.edu/",
        "leadership": "Jonathan Bailey Holland — Dean",
        "research_centers": [
            "Bienen Opera Theater",
            "Institute for New Music",
            "Music Performance Studies",
            "Contemporary Music Ensemble",
        ],
        "keywords": ["Bienen School of Music", "music", "conservatory"],
    },
    {
        "name": SESP,
        "sort_order": 6,
        "website": "https://www.sesp.northwestern.edu/",
        "leadership": "Bryan McKinley Jones Brayboy — Dean",
        "research_centers": [
            "Institute for Policy Research",
            "Center for Learning and Organizational Change",
            "Developmental Sciences",
            "Equitable Learning Environments",
        ],
        "keywords": ["SESP", "School of Education and Social Policy", "education", "social policy"],
    },
    {
        "name": KELLOGG,
        "sort_order": 7,
        "website": "https://www.kellogg.northwestern.edu/",
        "leadership": "Francesca Cornelli — Dean",
        "research_centers": [
            "Heizer Center for Private Equity and Venture Capital",
            "Guthrie Center for Real Estate Research",
            "Kellogg Public-Private Interface",
            "Healthcare at Kellogg",
        ],
        "keywords": ["Kellogg School of Management", "MBA", "business"],
    },
    {
        "name": LAW,
        "sort_order": 8,
        "website": "https://www.law.northwestern.edu/",
        "leadership": "Zachary D. Clopton — Interim Dean",
        "research_centers": [
            "Bluhm Legal Clinic",
            "Center for International Human Rights",
            "Center on Law, Business, and Economics",
            "Program on Negotiation and Mediation",
        ],
        "keywords": ["Pritzker School of Law", "JD", "law"],
    },
    {
        "name": FEINBERG,
        "sort_order": 9,
        "website": "https://www.feinberg.northwestern.edu/",
        "leadership": "Eric G. Neilson — Dean",
        "research_centers": [
            "Robert H. Lurie Comprehensive Cancer Center",
            "NUCATS Institute",
            "Feinberg Cardiovascular and Renal Research Center",
            "Institute for Global Health",
        ],
        "keywords": ["Feinberg School of Medicine", "MD", "medicine"],
    },
    {
        "name": TGS,
        "sort_order": 10,
        "website": "https://www.tgs.northwestern.edu/",
        "leadership": "Kelly Mayo — Dean",
        "research_centers": [
            "Interdisciplinary Biological Sciences Graduate Program",
            "Office of Graduate Research",
            "Mellon Cluster Initiative",
            "Graduate Research Grant programs",
        ],
        "keywords": ["The Graduate School", "TGS", "PhD", "graduate"],
    },
    {
        "name": SPS,
        "sort_order": 11,
        "website": "https://sps.northwestern.edu/",
        "leadership": "Thomas F. Gibbons — Dean",
        "research_centers": [
            "Center for Public Safety",
            "Osher Lifelong Learning Institute",
            "Professional Development Programs",
            "Northwestern Summer Session",
        ],
        "keywords": ["School of Professional Studies", "SPS", "online", "part-time"],
    },
]

SCHOOLS: list[dict] = [
    {
        "name": m["name"],
        "sort_order": m["sort_order"],
        "description": f"The {m['name']} is one of the eleven schools of Northwestern University.",
    }
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {
            "label": "Northwestern University — Schools and Colleges",
            "url": "https://www.northwestern.edu/academics/",
        },
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of the eleven schools of Northwestern University."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://news.northwestern.edu/feeds/allStories"
_EVENTS = {"url": "https://planitpurple.northwestern.edu/feed/ical/124", "type": "ical"}
_SOCIAL = {
    "instagram": "https://instagram.com/northwesternu",
    "facebook": "https://www.facebook.com/NorthwesternU",
    "x": "https://x.com/northwesternu",
    "youtube": "https://www.youtube.com/user/NorthwesternU",
    "linkedin": "https://www.linkedin.com/school/northwestern-university/",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.northwestern.edu/",
    "news_curated": True,
    "events_feed": dict(_EVENTS),
    "social": _SOCIAL,
}


def _school_content(name: str) -> dict:
    m = next(x for x in _SCHOOL_META if x["name"] == name)
    return {
        "news_rss": _NEWS_RSS,
        "news_url": m["website"],
        "news_curated": False,
        "events_feed": dict(_EVENTS),
        "keywords": list(m["keywords"]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# ── Real program catalog (researched; replaces the IPEDS×award-level mint) ──
# Every row is a real Northwestern degree program with its own per-credential,
# field-specific description researched from the official Northwestern undergraduate
# catalog (catalogs.northwestern.edu), the university Graduate Degree Programs A-Z
# (northwestern.edu/academics/graduate-a-to-z.html), and each school's pages. Named
# units are ONLY verified Northwestern units — zero peer-institution signatures.
_DUR: dict[str, int] = {
    "bachelors": 48,
    "masters": 24,
    "phd": 60,
    "professional": 36,
    "certificate": 12,
}


def _p(slug, school, name, degree, cip, dept, desc, *, dur=None, fmt="on_campus"):
    return {
        "slug": slug,
        "school": school,
        "program_name": name,
        "degree_type": degree,
        "duration_months": dur or _DUR.get(degree, 24),
        "delivery_format": fmt,
        "cip": cip,
        "department": dept,
        "description": desc,
    }


PROGRAMS: list[dict] = [
    # ── Weinberg College of Arts and Sciences — undergraduate majors ──
    _p(
        "northwestern-african-american-studies-ba",
        WEINBERG,
        "Bachelor of Arts in African American Studies",
        "bachelors",
        "05.02",
        "Department of African American Studies",
        "Weinberg majors in African American Studies examine the history, politics, literature, and social movements of the Black diaspora through the Department of African American Studies.",
    ),
    _p(
        "northwestern-american-studies-ba",
        WEINBERG,
        "Bachelor of Arts in American Studies",
        "bachelors",
        "05.01",
        "Program in American Studies",
        "American Studies majors read U.S. culture, politics, and identity across literature, history, art, and media in an interdisciplinary Weinberg program.",
    ),
    _p(
        "northwestern-anthropology-ba",
        WEINBERG,
        "Bachelor of Arts in Anthropology",
        "bachelors",
        "45.02",
        "Department of Anthropology",
        "Anthropology majors train in archaeology, biological anthropology, and sociocultural fieldwork, with Chicago-area ethnography and global field study.",
    ),
    _p(
        "northwestern-art-history-ba",
        WEINBERG,
        "Bachelor of Arts in Art History",
        "bachelors",
        "50.07",
        "Department of Art History",
        "Art History majors study visual cultures from antiquity to the present, using the Block Museum of Art and Chicago collections for object-based research.",
    ),
    _p(
        "northwestern-art-theory-practice-ba",
        WEINBERG,
        "Bachelor of Arts in Art Theory and Practice",
        "bachelors",
        "50.07",
        "Department of Art Theory and Practice",
        "Art Theory and Practice majors combine studio work in painting, sculpture, and new media with critical theory in Weinberg's studio art department.",
    ),
    _p(
        "northwestern-asian-american-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Asian American Studies",
        "bachelors",
        "05.02",
        "Asian American Studies Program",
        "Asian American Studies majors examine migration, race, labor, and community across Asian American histories and cultures.",
    ),
    _p(
        "northwestern-asian-languages-cultures-ba",
        WEINBERG,
        "Bachelor of Arts in Asian Languages and Cultures",
        "bachelors",
        "16.03",
        "Department of Asian Languages and Cultures",
        "Majors study Chinese, Japanese, and South Asian languages alongside the literature, religion, and history of Asia.",
    ),
    _p(
        "northwestern-biological-sciences-bs",
        WEINBERG,
        "Bachelor of Science in Biological Sciences",
        "bachelors",
        "26.01",
        "Program in Biological Sciences",
        "Biological Sciences majors study genetics, cell and molecular biology, physiology, and ecology, joining faculty labs across Weinberg and Feinberg.",
    ),
    _p(
        "northwestern-chemistry-bs",
        WEINBERG,
        "Bachelor of Science in Chemistry",
        "bachelors",
        "40.05",
        "Department of Chemistry",
        "Chemistry majors cover organic, inorganic, physical, and analytical chemistry, with undergraduate research in catalysis, materials, and chemical biology.",
    ),
    _p(
        "northwestern-classics-ba",
        WEINBERG,
        "Bachelor of Arts in Classics",
        "bachelors",
        "16.12",
        "Department of Classics",
        "Classics majors read Greek and Latin literature, ancient history, and philosophy, with archaeology and the reception of the ancient world.",
    ),
    _p(
        "northwestern-cognitive-science-ba",
        WEINBERG,
        "Bachelor of Arts in Cognitive Science",
        "bachelors",
        "30.25",
        "Cognitive Science Program",
        "Cognitive Science majors integrate psychology, linguistics, philosophy, computer science, and neuroscience to study the mind and intelligent behavior.",
    ),
    _p(
        "northwestern-comparative-literary-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Comparative Literary Studies",
        "bachelors",
        "16.01",
        "Program in Comparative Literary Studies",
        "Comparative Literary Studies majors read literature across languages and national traditions alongside critical and translation theory.",
    ),
    _p(
        "northwestern-earth-planetary-sciences-bs",
        WEINBERG,
        "Bachelor of Science in Earth and Planetary Sciences",
        "bachelors",
        "40.06",
        "Department of Earth and Planetary Sciences",
        "Earth and Planetary Sciences majors study geology, climate, geophysics, and planetary science through field work and laboratory analysis of Earth systems.",
    ),
    _p(
        "northwestern-economics-bs",
        WEINBERG,
        "Bachelor of Arts in Economics",
        "bachelors",
        "45.06",
        "Department of Economics",
        "Weinberg economics majors build a quantitative foundation in microeconomics, macroeconomics, and econometrics, with electives in finance, labor, and development.",
    ),
    _p(
        "northwestern-english-ba",
        WEINBERG,
        "Bachelor of Arts in English",
        "bachelors",
        "23.01",
        "Department of English",
        "English majors study literature in English and creative writing, with tracks in poetry, fiction, and literary history.",
    ),
    _p(
        "northwestern-environmental-sciences-bs",
        WEINBERG,
        "Bachelor of Science in Environmental Sciences",
        "bachelors",
        "03.01",
        "Program in Environmental Sciences",
        "Environmental Sciences majors combine earth science, ecology, and chemistry to study climate, ecosystems, and environmental change.",
    ),
    _p(
        "northwestern-environmental-policy-culture-ba",
        WEINBERG,
        "Bachelor of Arts in Environmental Policy and Culture",
        "bachelors",
        "03.01",
        "Environmental Policy and Culture Program",
        "This major examines the politics, ethics, and humanities of environmental issues across the social sciences and humanities.",
    ),
    _p(
        "northwestern-french-ba",
        WEINBERG,
        "Bachelor of Arts in French",
        "bachelors",
        "16.09",
        "Department of French and Italian",
        "French majors develop advanced proficiency and study French and Francophone literature, film, and culture.",
    ),
    _p(
        "northwestern-gender-sexuality-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Gender and Sexuality Studies",
        "bachelors",
        "05.02",
        "Gender and Sexuality Studies Program",
        "Majors analyze gender, sexuality, and feminist theory across the humanities and social sciences.",
    ),
    _p(
        "northwestern-german-ba",
        WEINBERG,
        "Bachelor of Arts in German",
        "bachelors",
        "16.05",
        "Department of German",
        "German majors gain advanced language skills and study German literature, philosophy, and intellectual history.",
    ),
    _p(
        "northwestern-global-health-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Global Health Studies",
        "bachelors",
        "51.22",
        "Program in Global Health Studies",
        "Global Health Studies majors examine health systems, epidemiology, and global health policy across disciplines, with fieldwork and a research practicum.",
    ),
    _p(
        "northwestern-history-ba",
        WEINBERG,
        "Bachelor of Arts in History",
        "bachelors",
        "54.01",
        "Department of History",
        "History majors investigate political, social, and cultural change across regions and eras, building research skills through archival seminars.",
    ),
    _p(
        "northwestern-integrated-science-bs",
        WEINBERG,
        "Bachelor of Science in Integrated Science",
        "bachelors",
        "30.01",
        "Integrated Science Program",
        "The Integrated Science Program is a selective honors track combining advanced biology, chemistry, physics, and mathematics for research-bound students.",
    ),
    _p(
        "northwestern-international-studies-ba",
        WEINBERG,
        "Bachelor of Arts in International Studies",
        "bachelors",
        "45.09",
        "International Studies Program",
        "International Studies majors study global politics, economics, and culture with a regional concentration and language study.",
    ),
    _p(
        "northwestern-italian-ba",
        WEINBERG,
        "Bachelor of Arts in Italian",
        "bachelors",
        "16.09",
        "Department of French and Italian",
        "Italian majors build proficiency and study Italian literature, cinema, and cultural history.",
    ),
    _p(
        "northwestern-jewish-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Jewish Studies",
        "bachelors",
        "05.01",
        "Crown Family Center for Jewish and Israel Studies",
        "Jewish Studies majors study Hebrew, Jewish history, religion, and literature through the Crown Family Center for Jewish and Israel Studies.",
    ),
    _p(
        "northwestern-latina-latino-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Latina and Latino Studies",
        "bachelors",
        "05.02",
        "Latina and Latino Studies Program",
        "Majors examine the histories, politics, and cultural production of Latinx communities in the United States.",
    ),
    _p(
        "northwestern-legal-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Legal Studies",
        "bachelors",
        "22.00",
        "Legal Studies Program",
        "Legal Studies majors explore law, society, and justice through political science, philosophy, and history.",
    ),
    _p(
        "northwestern-linguistics-ba",
        WEINBERG,
        "Bachelor of Arts in Linguistics",
        "bachelors",
        "16.01",
        "Department of Linguistics",
        "Linguistics majors study phonology, syntax, semantics, and psycholinguistics, with computational and field methods.",
    ),
    _p(
        "northwestern-mathematics-bs",
        WEINBERG,
        "Bachelor of Science in Mathematics",
        "bachelors",
        "27.01",
        "Department of Mathematics",
        "Mathematics majors cover analysis, algebra, topology, and applied mathematics, with paths toward pure theory or applications.",
    ),
    _p(
        "northwestern-mmss-ba",
        WEINBERG,
        "Bachelor of Arts in Mathematical Methods in the Social Sciences",
        "bachelors",
        "45.01",
        "Mathematical Methods in the Social Sciences Program",
        "MMSS is a selective adjunct major pairing rigorous mathematical modeling, statistics, and economics with a social-science major.",
    ),
    _p(
        "northwestern-mena-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Middle East and North African Studies",
        "bachelors",
        "05.01",
        "Middle East and North African Studies Program",
        "Majors study the languages, history, politics, and cultures of the Middle East and North Africa.",
    ),
    _p(
        "northwestern-neuroscience-bs",
        WEINBERG,
        "Bachelor of Science in Neuroscience",
        "bachelors",
        "26.15",
        "Department of Neurobiology",
        "Neuroscience majors study molecular, cellular, and systems neuroscience and behavior, joining labs across Weinberg and Feinberg.",
    ),
    _p(
        "northwestern-philosophy-ba",
        WEINBERG,
        "Bachelor of Arts in Philosophy",
        "bachelors",
        "38.01",
        "Department of Philosophy",
        "Philosophy majors work in metaphysics, epistemology, ethics, and logic, with strengths in moral and political philosophy.",
    ),
    _p(
        "northwestern-physics-bs",
        WEINBERG,
        "Bachelor of Science in Physics",
        "bachelors",
        "40.08",
        "Department of Physics and Astronomy",
        "Physics majors study classical and quantum mechanics, electromagnetism, and astrophysics, with research access to the CIERA astrophysics community.",
    ),
    _p(
        "northwestern-political-science-ba",
        WEINBERG,
        "Bachelor of Arts in Political Science",
        "bachelors",
        "45.10",
        "Department of Political Science",
        "Political Science majors study American politics, international relations, comparative politics, and political theory, supported by the Institute for Policy Research.",
    ),
    _p(
        "northwestern-psychology-general-bs",
        WEINBERG,
        "Bachelor of Arts in Psychology",
        "bachelors",
        "42.01",
        "Department of Psychology",
        "Weinberg psychology majors study cognitive, clinical, developmental, and social psychology, joining faculty research labs across the department.",
    ),
    _p(
        "northwestern-religious-studies-ba",
        WEINBERG,
        "Bachelor of Arts in Religious Studies",
        "bachelors",
        "38.02",
        "Department of Religious Studies",
        "Religious Studies majors examine the texts, histories, and practices of world religious traditions through comparative and critical study.",
    ),
    _p(
        "northwestern-slavic-ba",
        WEINBERG,
        "Bachelor of Arts in Slavic Languages and Literatures",
        "bachelors",
        "16.04",
        "Department of Slavic Languages and Literatures",
        "Slavic majors study Russian and other Slavic languages, literatures, and the cultural history of Eastern Europe.",
    ),
    _p(
        "northwestern-sociology-ba",
        WEINBERG,
        "Bachelor of Arts in Sociology",
        "bachelors",
        "45.11",
        "Department of Sociology",
        "Sociology majors study social inequality, organizations, and culture using quantitative and qualitative research methods.",
    ),
    _p(
        "northwestern-spanish-portuguese-ba",
        WEINBERG,
        "Bachelor of Arts in Spanish and Portuguese",
        "bachelors",
        "16.09",
        "Department of Spanish and Portuguese",
        "Majors gain advanced proficiency and study Iberian and Latin American literature, linguistics, and culture.",
    ),
    _p(
        "northwestern-statistics-data-science-bs",
        WEINBERG,
        "Bachelor of Science in Statistics and Data Science",
        "bachelors",
        "27.05",
        "Department of Statistics and Data Science",
        "Statistics and Data Science majors study probability, statistical inference, and machine learning, applying data analysis across scientific and social domains.",
    ),
    # ── McCormick School of Engineering and Applied Science — undergraduate ──
    _p(
        "northwestern-biomedical-medical-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Biomedical Engineering",
        "bachelors",
        "14.05",
        "Department of Biomedical Engineering",
        "McCormick biomedical engineering majors work across biomaterials, neural engineering, imaging, and biomechanics, with senior design and ties to the Querrey Simpson Institute for Bioelectronics.",
    ),
    _p(
        "northwestern-chemical-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Chemical Engineering",
        "bachelors",
        "14.07",
        "Department of Chemical and Biological Engineering",
        "Chemical engineering majors study reaction engineering, thermodynamics, transport, and process design, with research in catalysis, energy, and biotechnology.",
    ),
    _p(
        "northwestern-civil-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Civil Engineering",
        "bachelors",
        "14.08",
        "Department of Civil and Environmental Engineering",
        "Civil engineering majors study structures, geotechnics, transportation, and construction, with project-based design of the built environment.",
    ),
    _p(
        "northwestern-environmental-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Environmental Engineering",
        "bachelors",
        "14.14",
        "Department of Civil and Environmental Engineering",
        "Environmental engineering majors study water resources, environmental chemistry, and sustainable infrastructure to address pollution and climate challenges.",
    ),
    _p(
        "northwestern-computer-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Computer Engineering",
        "bachelors",
        "14.09",
        "Department of Electrical and Computer Engineering",
        "Computer engineering majors bridge hardware and software, studying digital systems, embedded computing, and computer architecture.",
    ),
    _p(
        "northwestern-electrical-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Electrical Engineering",
        "bachelors",
        "14.10",
        "Department of Electrical and Computer Engineering",
        "Electrical engineering majors study circuits, signals, electromagnetics, and photonics, with research in devices, communications, and control.",
    ),
    _p(
        "northwestern-computer-science-bs",
        MCCORMICK,
        "Bachelor of Science in Computer Science",
        "bachelors",
        "11.07",
        "Department of Computer Science",
        "Northwestern's computer science majors study algorithms, systems, AI, and theory in McCormick, with the CS+X joint majors linking computing to design, journalism, and the arts.",
    ),
    _p(
        "northwestern-materials-science-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Materials Science and Engineering",
        "bachelors",
        "14.18",
        "Department of Materials Science and Engineering",
        "Materials science majors study the structure, properties, and processing of metals, ceramics, polymers, and nanomaterials, drawing on the International Institute for Nanotechnology.",
    ),
    _p(
        "northwestern-mechanical-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Mechanical Engineering",
        "bachelors",
        "14.19",
        "Department of Mechanical Engineering",
        "Mechanical engineering majors study solid and fluid mechanics, thermodynamics, dynamics, and design, with tracks in robotics, energy, and manufacturing.",
    ),
    _p(
        "northwestern-industrial-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Industrial Engineering and Management Sciences",
        "bachelors",
        "14.35",
        "Department of Industrial Engineering and Management Sciences",
        "Industrial engineering majors study optimization, stochastic models, and analytics for operations, supply chains, and decision systems.",
    ),
    _p(
        "northwestern-applied-mathematics-bs",
        MCCORMICK,
        "Bachelor of Science in Applied Mathematics",
        "bachelors",
        "14.03",
        "Department of Engineering Sciences and Applied Mathematics",
        "Applied mathematics majors model physical and biological systems using differential equations, numerical methods, and dynamical-systems theory.",
    ),
    _p(
        "northwestern-manufacturing-design-engineering-bs",
        MCCORMICK,
        "Bachelor of Science in Manufacturing and Design Engineering",
        "bachelors",
        "14.36",
        "Segal Design Institute",
        "This major combines mechanical engineering with human-centered design through the Segal Design Institute.",
    ),
    # ── Medill — undergraduate ──
    _p(
        "northwestern-journalism-bs",
        MEDILL,
        "Bachelor of Science in Journalism",
        "bachelors",
        "09.04",
        "Medill School of Journalism, Media, Integrated Marketing Communications",
        "Medill journalism majors learn reporting, writing, audio, video, and data journalism, with the Journalism Residency placing students in newsrooms nationwide.",
    ),
    # ── School of Communication — undergraduate ──
    _p(
        "northwestern-communication-studies-ba",
        COMMUNICATION,
        "Bachelor of Arts in Communication Studies",
        "bachelors",
        "09.01",
        "Department of Communication Studies",
        "Communication Studies majors examine rhetoric, interpersonal and organizational communication, and media, with research and analytics methods.",
    ),
    _p(
        "northwestern-communication-sciences-disorders-bs",
        COMMUNICATION,
        "Bachelor of Science in Communication Sciences and Disorders",
        "bachelors",
        "51.02",
        "Roxelyn and Richard Pepper Department of Communication Sciences and Disorders",
        "Majors study the science of speech, language, and hearing, preparing for graduate work in audiology and speech-language pathology.",
    ),
    _p(
        "northwestern-performance-studies-ba",
        COMMUNICATION,
        "Bachelor of Arts in Performance Studies",
        "bachelors",
        "50.05",
        "Department of Performance Studies",
        "Performance Studies majors analyze performance as culture and art, combining critical theory with adaptation and embodied practice.",
    ),
    _p(
        "northwestern-radio-television-and-digital-communication-bs",
        COMMUNICATION,
        "Bachelor of Arts in Radio/Television/Film",
        "bachelors",
        "50.06",
        "Department of Radio/Television/Film",
        "RTVF majors study screenwriting, directing, producing, and media studies, with hands-on film, television, and documentary production.",
    ),
    _p(
        "northwestern-theatre-ba",
        COMMUNICATION,
        "Bachelor of Arts in Theatre",
        "bachelors",
        "50.05",
        "Department of Theatre",
        "Theatre majors train in acting, directing, design, and dramatic literature within the School of Communication's nationally known theatre program.",
    ),
    _p(
        "northwestern-dance-ba",
        COMMUNICATION,
        "Bachelor of Arts in Dance",
        "bachelors",
        "50.03",
        "Dance Program",
        "Dance majors combine technique and choreography with dance history and the science of movement in the School of Communication.",
    ),
    # ── Bienen School of Music — undergraduate ──
    _p(
        "northwestern-music-performance-bm",
        BIENEN,
        "Bachelor of Music in Performance",
        "bachelors",
        "50.09",
        "Department of Music Performance",
        "Bienen performance majors study applied music in strings, winds, brass, percussion, piano, or voice, with orchestra, chamber, and recital performance.",
    ),
    _p(
        "northwestern-music-composition-bm",
        BIENEN,
        "Bachelor of Music in Composition",
        "bachelors",
        "50.09",
        "Department of Composition and Music Technology",
        "Composition majors write for instrumental, vocal, and electronic media, studying orchestration, music technology, and contemporary practice.",
    ),
    _p(
        "northwestern-jazz-studies-bm",
        BIENEN,
        "Bachelor of Music in Jazz Studies",
        "bachelors",
        "50.09",
        "Jazz Studies Program",
        "Jazz Studies majors develop improvisation, composition, and ensemble performance in the jazz idiom alongside the broader Bienen curriculum.",
    ),
    _p(
        "northwestern-music-education-bm",
        BIENEN,
        "Bachelor of Music in Music Education",
        "bachelors",
        "13.13",
        "Department of Music Studies",
        "Music Education majors combine performance with pedagogy and a teaching practicum toward Illinois K-12 music licensure.",
    ),
    _p(
        "northwestern-music-theory-cognition-ba",
        BIENEN,
        "Bachelor of Arts in Music Theory and Cognition",
        "bachelors",
        "50.09",
        "Department of Music Studies",
        "This major analyzes musical structure and studies the psychology of music perception and cognition.",
    ),
    # ── School of Education and Social Policy — undergraduate ──
    _p(
        "northwestern-learning-organizational-change-bs",
        SESP,
        "Bachelor of Science in Learning and Organizational Change",
        "bachelors",
        "13.03",
        "School of Education and Social Policy",
        "This major studies how people and organizations learn and change, applying social science to design, leadership, and consulting.",
    ),
    _p(
        "northwestern-human-development-context-bs",
        SESP,
        "Bachelor of Science in Human Development in Context",
        "bachelors",
        "19.07",
        "School of Education and Social Policy",
        "Majors study psychology, sociology, and policy across the lifespan, with field work in schools, clinics, and community organizations.",
    ),
    _p(
        "northwestern-social-policy-bs",
        SESP,
        "Bachelor of Science in Social Policy",
        "bachelors",
        "44.05",
        "School of Education and Social Policy",
        "Social Policy majors analyze education, health, and economic policy using social science research and a field practicum.",
    ),
    _p(
        "northwestern-learning-sciences-bs",
        SESP,
        "Bachelor of Science in Learning Sciences",
        "bachelors",
        "13.01",
        "School of Education and Social Policy",
        "Learning Sciences majors study how people learn and how to design learning environments, technologies, and curricula.",
    ),
    _p(
        "northwestern-secondary-teaching-bs",
        SESP,
        "Bachelor of Science in Secondary Teaching",
        "bachelors",
        "13.12",
        "School of Education and Social Policy",
        "This major pairs a disciplinary subject with education coursework and supervised student teaching toward secondary licensure.",
    ),
    # ── Kellogg School of Management — graduate ──
    _p(
        "northwestern-mba-ms",
        KELLOGG,
        "Master of Business Administration",
        "masters",
        "52.02",
        "Kellogg School of Management",
        "Kellogg's full-time MBA builds general-management leadership across marketing, finance, strategy, and entrepreneurship, with a collaborative team-based culture and majors in over a dozen areas.",
        dur=24,
    ),
    _p(
        "northwestern-management-sciences-and-quantitative-methods-ms",
        KELLOGG,
        "Master of Science in Management Studies",
        "masters",
        "52.13",
        "Kellogg School of Management",
        "Kellogg's MS in Management Studies gives recent graduates a one-year quantitative business foundation in accounting, finance, marketing, and analytics.",
        dur=12,
    ),
    _p(
        "northwestern-master-in-management-ms",
        KELLOGG,
        "Master in Management",
        "masters",
        "52.02",
        "Kellogg School of Management",
        "The Kellogg Master in Management is a pre-experience program covering core business disciplines and data-driven decision making for early-career professionals.",
        dur=12,
    ),
    _p(
        "northwestern-marketing-phd",
        KELLOGG,
        "Doctor of Philosophy in Marketing",
        "phd",
        "52.14",
        "Kellogg School of Management",
        "Kellogg's marketing doctoral program trains researchers in consumer behavior, quantitative modeling, and marketing strategy for academic careers.",
    ),
    _p(
        "northwestern-managerial-economics-strategy-phd",
        KELLOGG,
        "Doctor of Philosophy in Managerial Economics and Strategy",
        "phd",
        "52.06",
        "Kellogg School of Management",
        "This doctoral program applies microeconomics and game theory to strategy, industrial organization, and competition for research careers.",
    ),
    _p(
        "northwestern-finance-phd",
        KELLOGG,
        "Doctor of Philosophy in Finance",
        "phd",
        "52.08",
        "Kellogg School of Management",
        "Kellogg's finance doctoral program develops research in asset pricing, corporate finance, and financial economics.",
    ),
    # ── Pritzker School of Law — graduate / professional ──
    _p(
        "northwestern-law-prof",
        LAW,
        "Juris Doctor",
        "professional",
        "22.01",
        "Pritzker School of Law",
        "Northwestern Pritzker's JD trains lawyers across doctrine, legal writing, and practice, with the Bluhm Legal Clinic and an accelerated two-year option.",
        dur=36,
    ),
    _p(
        "northwestern-llm",
        LAW,
        "Master of Laws",
        "masters",
        "22.02",
        "Pritzker School of Law",
        "The Pritzker LLM offers internationally trained lawyers advanced study in U.S. law, business, and human rights.",
        dur=12,
    ),
    _p(
        "northwestern-master-science-law-ms",
        LAW,
        "Master of Science in Law",
        "masters",
        "22.00",
        "Pritzker School of Law",
        "The Master of Science in Law equips STEM and business professionals with legal knowledge in regulation, intellectual property, and compliance.",
        dur=12,
    ),
    # ── Feinberg School of Medicine — graduate / professional ──
    _p(
        "northwestern-medicine-prof",
        FEINBERG,
        "Doctor of Medicine",
        "professional",
        "51.12",
        "Feinberg School of Medicine",
        "Feinberg's MD program integrates the Health & Society curriculum with early clinical immersion at Northwestern Memorial and affiliated Chicago hospitals.",
        dur=48,
    ),
    _p(
        "northwestern-public-health-mph",
        FEINBERG,
        "Master of Public Health",
        "masters",
        "51.22",
        "Department of Preventive Medicine",
        "Feinberg's MPH trains practitioners in epidemiology, biostatistics, and health policy for careers in public health practice and research.",
    ),
    _p(
        "northwestern-physical-therapy-dpt",
        FEINBERG,
        "Doctor of Physical Therapy",
        "professional",
        "51.23",
        "Department of Physical Therapy and Human Movement Sciences",
        "Feinberg's DPT prepares physical therapists through anatomy, neuroscience, and supervised clinical rotations.",
        dur=36,
    ),
    _p(
        "northwestern-driskill-life-sciences-phd",
        FEINBERG,
        "Doctor of Philosophy in the Life Sciences",
        "phd",
        "26.01",
        "Driskill Graduate Program in the Life Sciences",
        "The Driskill Graduate Program trains biomedical scientists in molecular, cellular, and translational research toward the PhD.",
    ),
    _p(
        "northwestern-genetic-counseling-ms",
        FEINBERG,
        "Master of Science in Genetic Counseling",
        "masters",
        "51.15",
        "Department of Preventive Medicine",
        "This program prepares genetic counselors through medical genetics, counseling practica, and clinical rotations.",
    ),
    _p(
        "northwestern-prosthetics-orthotics-ms",
        FEINBERG,
        "Master of Science in Prosthetics-Orthotics",
        "masters",
        "51.23",
        "Northwestern University Prosthetics-Orthotics Center",
        "Northwestern's prosthetics-orthotics program trains clinicians to design and fit prosthetic and orthotic devices through its long-established center.",
    ),
    _p(
        "northwestern-physician-assistant-ms",
        FEINBERG,
        "Master of Science in Physician Assistant Studies",
        "masters",
        "51.09",
        "Feinberg School of Medicine",
        "Feinberg's physician assistant program prepares PAs through medical-science coursework and supervised clinical rotations.",
    ),
    # ── McCormick — graduate ──
    _p(
        "northwestern-computer-science-ms",
        MCCORMICK,
        "Master of Science in Computer Science",
        "masters",
        "11.07",
        "Department of Computer Science",
        "McCormick's MS in Computer Science offers advanced coursework and research in artificial intelligence, systems, theory, and human-computer interaction.",
    ),
    _p(
        "northwestern-computer-science-phd",
        MCCORMICK,
        "Doctor of Philosophy in Computer Science",
        "phd",
        "11.07",
        "Department of Computer Science",
        "The computer science doctoral program supports dissertation research in artificial intelligence, systems, theory, and human-computer interaction.",
    ),
    _p(
        "northwestern-machine-learning-data-science-ms",
        MCCORMICK,
        "Master of Science in Machine Learning and Data Science",
        "masters",
        "11.07",
        "Department of Computer Science",
        "This professional master's develops applied machine learning, statistics, and data engineering for analytics and AI roles.",
    ),
    _p(
        "northwestern-artificial-intelligence-ms",
        MCCORMICK,
        "Master of Science in Artificial Intelligence",
        "masters",
        "11.01",
        "McCormick School of Engineering and Applied Science",
        "The MS in Artificial Intelligence covers machine learning, deep learning, and AI systems through an applied, project-based curriculum.",
    ),
    _p(
        "northwestern-robotics-ms",
        MCCORMICK,
        "Master of Science in Robotics",
        "masters",
        "14.42",
        "McCormick School of Engineering and Applied Science",
        "Northwestern's MS in Robotics integrates mechanical design, controls, perception, and machine learning for autonomous systems.",
    ),
    _p(
        "northwestern-biomedical-engineering-phd",
        MCCORMICK,
        "Doctor of Philosophy in Biomedical Engineering",
        "phd",
        "14.05",
        "Department of Biomedical Engineering",
        "The biomedical engineering doctoral program supports research in bioelectronics, regenerative engineering, imaging, and neural engineering.",
    ),
    _p(
        "northwestern-mechanical-engineering-phd",
        MCCORMICK,
        "Doctor of Philosophy in Mechanical Engineering",
        "phd",
        "14.19",
        "Department of Mechanical Engineering",
        "Mechanical engineering doctoral research spans robotics, fluid dynamics, manufacturing, and energy systems.",
    ),
    _p(
        "northwestern-materials-science-engineering-phd",
        MCCORMICK,
        "Doctor of Philosophy in Materials Science and Engineering",
        "phd",
        "14.18",
        "Department of Materials Science and Engineering",
        "Materials science doctoral research spans nanomaterials, soft materials, and computational materials design through the International Institute for Nanotechnology.",
    ),
    _p(
        "northwestern-chemical-biological-engineering-phd",
        MCCORMICK,
        "Doctor of Philosophy in Chemical and Biological Engineering",
        "phd",
        "14.07",
        "Department of Chemical and Biological Engineering",
        "This doctoral program supports research in catalysis, energy, soft materials, and synthetic biology.",
    ),
    _p(
        "northwestern-engineering-management-mem",
        MCCORMICK,
        "Master of Engineering Management",
        "masters",
        "14.27",
        "McCormick School of Engineering and Applied Science",
        "The Master of Engineering Management develops technical leaders through engineering, analytics, and management coursework.",
        dur=15,
    ),
    _p(
        "northwestern-engineering-design-innovation-ms",
        MCCORMICK,
        "Master of Science in Engineering Design Innovation",
        "masters",
        "14.01",
        "Segal Design Institute",
        "Through the Segal Design Institute, this master's trains designers in human-centered product design and innovation.",
    ),
    # ── Weinberg / The Graduate School — doctoral and MFA ──
    _p(
        "northwestern-economics-phd",
        WEINBERG,
        "Doctor of Philosophy in Economics",
        "phd",
        "45.06",
        "Department of Economics",
        "Northwestern's economics doctoral program trains research economists in microeconomics, macroeconomics, and econometrics, with strong theory and applied fields.",
    ),
    _p(
        "northwestern-chemistry-phd",
        WEINBERG,
        "Doctor of Philosophy in Chemistry",
        "phd",
        "40.05",
        "Department of Chemistry",
        "Chemistry doctoral research spans organic, inorganic, physical, and biological chemistry, with strengths in catalysis and materials.",
    ),
    _p(
        "northwestern-physics-phd",
        WEINBERG,
        "Doctor of Philosophy in Physics",
        "phd",
        "40.08",
        "Department of Physics and Astronomy",
        "Physics doctoral research covers condensed matter, astrophysics, high-energy, and biological physics.",
    ),
    _p(
        "northwestern-mathematics-phd",
        WEINBERG,
        "Doctor of Philosophy in Mathematics",
        "phd",
        "27.01",
        "Department of Mathematics",
        "The mathematics doctoral program supports research in geometry, analysis, algebra, and applied mathematics.",
    ),
    _p(
        "northwestern-statistics-data-science-phd",
        WEINBERG,
        "Doctor of Philosophy in Statistics and Data Science",
        "phd",
        "27.05",
        "Department of Statistics and Data Science",
        "This doctoral program develops research in statistical theory, machine learning, and data-driven inference.",
    ),
    _p(
        "northwestern-psychology-phd",
        WEINBERG,
        "Doctor of Philosophy in Psychology",
        "phd",
        "42.01",
        "Department of Psychology",
        "Psychology doctoral research spans cognitive, clinical, developmental, social, and brain-and-behavior areas.",
    ),
    _p(
        "northwestern-political-science-phd",
        WEINBERG,
        "Doctor of Philosophy in Political Science",
        "phd",
        "45.10",
        "Department of Political Science",
        "Political science doctoral research covers American politics, international relations, comparative politics, and theory, with the Institute for Policy Research.",
    ),
    _p(
        "northwestern-sociology-phd",
        WEINBERG,
        "Doctor of Philosophy in Sociology",
        "phd",
        "45.11",
        "Department of Sociology",
        "Sociology doctoral research addresses inequality, organizations, culture, and social methods.",
    ),
    _p(
        "northwestern-history-phd",
        WEINBERG,
        "Doctor of Philosophy in History",
        "phd",
        "54.01",
        "Department of History",
        "History doctoral research spans U.S., European, and global fields with archival and transnational methods.",
    ),
    _p(
        "northwestern-anthropology-phd",
        WEINBERG,
        "Doctor of Philosophy in Anthropology",
        "phd",
        "45.02",
        "Department of Anthropology",
        "Anthropology doctoral research integrates sociocultural, archaeological, and medical anthropology.",
    ),
    _p(
        "northwestern-english-phd",
        WEINBERG,
        "Doctor of Philosophy in English",
        "phd",
        "23.01",
        "Department of English",
        "English doctoral research covers literary history, theory, and creative writing across periods and genres.",
    ),
    _p(
        "northwestern-creative-writing-mfa",
        WEINBERG,
        "Master of Fine Arts in Creative Writing",
        "masters",
        "23.13",
        "Department of English",
        "The Litowitz MFA+MA program trains poets and fiction writers alongside graduate literary study.",
        dur=24,
    ),
    _p(
        "northwestern-earth-planetary-sciences-phd",
        WEINBERG,
        "Doctor of Philosophy in Earth and Planetary Sciences",
        "phd",
        "40.06",
        "Department of Earth and Planetary Sciences",
        "Doctoral research covers climate, geophysics, geobiology, and planetary science.",
    ),
    _p(
        "northwestern-neuroscience-phd",
        WEINBERG,
        "Doctor of Philosophy in Neuroscience",
        "phd",
        "26.15",
        "Northwestern University Interdepartmental Neuroscience Program",
        "The Northwestern University Interdepartmental Neuroscience program trains doctoral researchers across molecular, systems, and cognitive neuroscience.",
    ),
    # ── Medill — graduate ──
    _p(
        "northwestern-journalism-ms",
        MEDILL,
        "Master of Science in Journalism",
        "masters",
        "09.04",
        "Medill School of Journalism, Media, Integrated Marketing Communications",
        "Medill's MSJ is an intensive professional master's in reporting, multimedia, and data journalism, anchored by the Journalism Residency.",
        dur=12,
    ),
    _p(
        "northwestern-imc-ms",
        MEDILL,
        "Master of Science in Integrated Marketing Communications",
        "masters",
        "09.09",
        "Medill School of Journalism, Media, Integrated Marketing Communications",
        "Medill's IMC master's trains marketers in data analytics, consumer insight, and brand strategy.",
        dur=15,
    ),
    # ── School of Communication — graduate ──
    _p(
        "northwestern-radio-television-and-digital-communication-ms",
        COMMUNICATION,
        "Master of Fine Arts in Documentary Media",
        "masters",
        "50.06",
        "Department of Radio/Television/Film",
        "This MFA trains documentary filmmakers in directing, producing, and editing nonfiction film through the RTVF department.",
        dur=24,
    ),
    _p(
        "northwestern-audiology-aud",
        COMMUNICATION,
        "Doctor of Audiology",
        "professional",
        "51.02",
        "Roxelyn and Richard Pepper Department of Communication Sciences and Disorders",
        "Northwestern's AuD prepares audiologists through hearing science, diagnostics, and clinical practicum.",
        dur=48,
    ),
    _p(
        "northwestern-speech-language-pathology-ms",
        COMMUNICATION,
        "Master of Science in Speech-Language Pathology",
        "masters",
        "51.02",
        "Roxelyn and Richard Pepper Department of Communication Sciences and Disorders",
        "This master's prepares speech-language pathologists through coursework and supervised clinical practica.",
    ),
    # ── School of Education and Social Policy — graduate ──
    _p(
        "northwestern-human-development-social-policy-phd",
        SESP,
        "Doctor of Philosophy in Human Development and Social Policy",
        "phd",
        "19.07",
        "School of Education and Social Policy",
        "This doctoral program integrates developmental science and policy analysis to study human development across contexts.",
    ),
    _p(
        "northwestern-learning-sciences-phd",
        SESP,
        "Doctor of Philosophy in Learning Sciences",
        "phd",
        "13.01",
        "School of Education and Social Policy",
        "The Learning Sciences doctoral program studies cognition, instruction, and the design of learning environments and technologies.",
    ),
    _p(
        "northwestern-learning-organizational-change-ms",
        SESP,
        "Master of Science in Learning and Organizational Change",
        "masters",
        "30.99",
        "School of Education and Social Policy",
        "MSLOC develops professionals in organizational learning, change management, and design through an evening format.",
        fmt="hybrid",
    ),
    # ── School of Professional Studies — online / professional ──
    _p(
        "northwestern-data-science-ms",
        SPS,
        "Master of Science in Data Science",
        "masters",
        "30.70",
        "School of Professional Studies",
        "Northwestern's MS in Data Science covers analytics, machine learning, and data engineering in a flexible online and part-time format.",
        fmt="online",
    ),
    _p(
        "northwestern-public-administration-ma",
        SPS,
        "Master of Arts in Public Administration",
        "masters",
        "44.04",
        "School of Professional Studies",
        "The SPS MPA prepares public-sector leaders in policy analysis, management, and governance, offered online and on campus.",
        fmt="online",
    ),
    _p(
        "northwestern-information-systems-ms",
        SPS,
        "Master of Science in Information Systems",
        "masters",
        "11.04",
        "School of Professional Studies",
        "This SPS master's covers data management, systems analysis, and IT strategy for working professionals.",
        fmt="hybrid",
    ),
    _p(
        "northwestern-sports-administration-ma",
        SPS,
        "Master of Arts in Sports Administration",
        "masters",
        "31.05",
        "School of Professional Studies",
        "Northwestern's sports administration master's covers league operations, analytics, and sport business, offered online.",
        fmt="online",
    ),
    _p(
        "northwestern-prose-poetry-mfa",
        SPS,
        "Master of Fine Arts in Prose and Poetry",
        "masters",
        "23.13",
        "School of Professional Studies",
        "The SPS MFA in Prose and Poetry trains writers through workshops and craft seminars in a low-residency format.",
        fmt="hybrid",
        dur=24,
    ),
]


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
    _catalog_errors.append(f"classification-only descriptions on {_classification_stubs} programs")
_name_prefix_desc = sum(
    1 for p in PROGRAMS if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(f"name-prefixed descriptions on {_name_prefix_desc} programs")
_peer_contamination = sum(
    1 for p in PROGRAMS if any(sig in (p.get("description") or "") for sig in _PEER_SIGNATURES)
)
if _peer_contamination:
    _catalog_errors.append(f"peer-contaminated descriptions on {_peer_contamination} programs")
_desc_counts = Counter(p.get("description") for p in PROGRAMS)
_shared_desc = sum(c for c in _desc_counts.values() if c >= 2)
if _shared_desc:
    _catalog_errors.append(
        f"identical descriptions shared across {_shared_desc} credential-sibling programs"
    )
_anti_stub = _anti_stub_analyze(PROGRAMS)
if not _anti_stub.is_clean:
    _catalog_errors.append(f"anti-stub gate failed: {_anti_stub.summary()}")
_artifacts = _machine_artifacts(PROGRAMS)
if _artifacts:
    _catalog_errors.append(f"machine-artifact descriptions on {len(_artifacts)} programs")
if _catalog_errors:
    raise RuntimeError(f"Northwestern catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# ── Matcher-core: cip_code + program-DISTINCT who_its_for (REPAIR_BACKLOG #1 + #4) ──────
# `cip_code` is the CIP join key the CPEF matcher uses (it reads the 2-digit family +
# program-name aliases — see services/match/field_canon.fields_offered_for_program); the
# verified IPEDS/Scorecard CIP-2020 family code already carried on every spec is stamped
# as-is (never a guessed 6-digit precision). `who_its_for` is the universal depth field —
# every program states the applicant it fits, derived from its OWN field + credential
# level, NEVER a degree-type template (the type-gaming the distinctness gate below forbids).

# Field labels for the 8 conferred-designation programs whose name carries no "... in {field}".
_FIELD_OVERRIDE: dict[str, str] = {
    "northwestern-mba-ms": "business administration",
    "northwestern-law-prof": "law",
    "northwestern-llm": "law",
    "northwestern-medicine-prof": "medicine",
    "northwestern-public-health-mph": "public health",
    "northwestern-physical-therapy-dpt": "physical therapy",
    "northwestern-engineering-management-mem": "engineering management",
    "northwestern-audiology-aud": "audiology",
}

# Short, student-facing school labels for the who_its_for frames.
_SCHOOL_SHORT: dict[str, str] = {
    WEINBERG: "Weinberg College",
    MCCORMICK: "the McCormick School of Engineering",
    MEDILL: "Medill",
    COMMUNICATION: "the School of Communication",
    BIENEN: "the Bienen School of Music",
    SESP: "the School of Education and Social Policy",
    KELLOGG: "Kellogg",
    FEINBERG: "the Feinberg School of Medicine",
    SPS: "the School of Professional Studies",
    LAW: "the Pritzker School of Law",
    TGS: "The Graduate School",
}


def _field_of(spec: dict) -> str:
    """The field-of-study label (the part after the credential designation)."""
    override = _FIELD_OVERRIDE.get(spec["slug"])
    if override:
        return override
    name = spec["program_name"]
    m = re.match(r"^.+? in (.+)$", name)
    return m.group(1) if m else name


# Credential-aware frames; {field} is interpolated per program, so distinct/total ≈ 1.0
# (no degree-type template — the type-gaming guard the distinctness assertion enforces).
_WHO_LEVEL: dict[str, str] = {
    "bachelors": (
        "Prospective undergraduates drawn to {field} who want a research-grounded "
        "Northwestern foundation in {school} and a path to graduate study or a career in the field."
    ),
    "masters": (
        "Graduates and early-career professionals focused on {field} who want advanced "
        "Northwestern training in {school} toward specialized practice or doctoral study."
    ),
    "phd": (
        "Research-minded scholars committed to {field} who want a funded Northwestern "
        "doctorate in {school} and an academic, industry-research, or policy career."
    ),
    "professional": (
        "Students preparing for licensed practice in {field} who want Northwestern's "
        "hands-on professional preparation in {school}."
    ),
    "certificate": (
        "Working professionals and students who want focused Northwestern coursework in "
        "{field} through {school} to complement a degree or advance on the job."
    ),
}

# Hand-written, program-specific statements for the flagship programs (researched audience
# rather than the generated frame); the rest derive a field-distinct statement from _who_for.
_WHO_BY_SLUG: dict[str, str] = {
    "northwestern-computer-science-bs": "Undergraduates aiming for software, AI, systems, or data-science careers who want McCormick and Weinberg's joint computer-science program — grounded in theory, systems, and machine learning — and strong Chicago and Bay-Area recruiting.",
    "northwestern-economics-bs": "Students drawn to economic analysis, policy, and data who want Weinberg's quantitative economics training and a path to finance, consulting, graduate school, or government.",
    "northwestern-mba-ms": "Early- to mid-career professionals targeting general-management, marketing, or strategy roles who want Kellogg's collaborative, team-based MBA and its deep recruiting in consulting and brand management.",
    "northwestern-law-prof": "Aspiring attorneys who want the Pritzker School of Law's small, practice-oriented J.D., its strong business-law and clinical offerings, and access to the Chicago legal market.",
    "northwestern-medicine-prof": "Future physicians committed to patient care and research who want the Feinberg School of Medicine's integrated curriculum and Chicago academic-medical-center training.",
    "northwestern-journalism-bs": "Undergraduates pursuing reporting, media, or integrated-marketing-communications careers who want Medill's professional newsroom training and its Journalism Residency.",
    "northwestern-journalism-ms": "Graduates and career-changers entering journalism or media who want Medill's intensive master's, its professional residencies, and Chicago and Washington newsroom access.",
    "northwestern-biomedical-medical-engineering-bs": "Undergraduates bridging engineering and medicine who want McCormick's biomedical-engineering program — device design with Feinberg and Chicago clinical immersion — and a path to industry, medical school, or a PhD.",
    "northwestern-statistics-data-science-bs": "Students drawn to statistical modeling, machine learning, and data analysis who want Weinberg's statistics and data-science foundation and a path to analytics, research, or graduate study.",
    "northwestern-computer-science-ms": "Graduates and professionals deepening software, AI, or systems expertise who want McCormick's master's in computer science and access to Chicago and national tech recruiting.",
    "northwestern-computer-science-phd": "Research-minded scholars in algorithms, systems, AI, or theory who want a funded McCormick computer-science doctorate and an academic or industry-research career.",
    "northwestern-psychology-general-bs": "Undergraduates interested in clinical, cognitive, and social psychology who want Weinberg's research-active foundation for graduate study or health and human-services work.",
}


def _who_for(spec: dict) -> str:
    """A field-specific, credential-aware who_its_for statement (never a type template)."""
    hand = _WHO_BY_SLUG.get(spec["slug"])
    if hand:
        return hand
    frame = _WHO_LEVEL.get(spec["degree_type"], _WHO_LEVEL["masters"])
    school = _SCHOOL_SHORT.get(spec["school"], "Northwestern")
    return frame.format(field=_field_of(spec), school=school)


WHO_BY_SLUG: dict[str, str] = {p["slug"]: _who_for(p) for p in PROGRAMS}

# Build gates: every program carries a real CIP family code and a program-distinct
# who_its_for; fail the build if either is missing or if who_its_for collapses below
# ~0.9 distinct/total (the type-gaming guard — gold field-specific catalogs are ~1.0).
_cip_missing = [p["slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    raise RuntimeError(f"Northwestern cip_code missing on {len(_cip_missing)} rows: {_cip_missing[:5]}")
_cip_bad = sorted({p["cip"] for p in PROGRAMS if not re.fullmatch(r"\d{2}\.\d{2,4}", p["cip"])})
if _cip_bad:
    raise RuntimeError(f"Northwestern malformed cip_code values: {_cip_bad}")
_who_missing = [s for s in PROGRAM_SLUGS if not WHO_BY_SLUG.get(s)]
if _who_missing:
    raise RuntimeError(f"Northwestern who_its_for missing on {len(_who_missing)} rows: {_who_missing[:5]}")
_who_vals = [WHO_BY_SLUG[s] for s in PROGRAM_SLUGS]
_who_ratio = len(set(_who_vals)) / max(len(_who_vals), 1)
if _who_ratio < 0.9:
    raise RuntimeError(
        f"Northwestern who_its_for type-gamed: distinct/total {_who_ratio:.2f} < 0.9 (must be program-distinct)"
    )

_TUITION_UG = 68322
_UNDERGRAD_COA = 91250
_AVG_NET_PRICE = 29167
_COST_SRC = (
    "U.S. Dept. of Education College Scorecard (UNITID 147767)",
    "https://collegescorecard.ed.gov/school/?147767-Northwestern-University",
)

# ── Published graduate / professional tuition (2025-26) ─────────────────────
# Northwestern Student Financial Services + school COA pages. Quarterly / trimester
# rates are converted to a full-time academic-year total (3 quarters or 3 trimesters)
# unless the program publishes an explicit annual or program-total figure.
_SFS_GRAD = "https://www.northwestern.edu/sfs/tuition/graduate/"
_TGS_MASTERS_QUARTER = 22973  # TGS full-time master's, 3–4 units/term
_TGS_MASTERS_ANNUAL = _TGS_MASTERS_QUARTER * 3  # 68,919
_TGS_MFA_QUARTER = 18689
_TGS_MFA_ANNUAL = _TGS_MFA_QUARTER * 3  # 56,067
_MCCORMICK_MS_QUARTER = 22973
_MCCORMICK_MS_ANNUAL = _MCCORMICK_MS_QUARTER * 3  # 68,919
_MCCORMICK_MEM_QUARTER = 22656
_MCCORMICK_MEM_ANNUAL = _MCCORMICK_MEM_QUARTER * 3  # 67,968
_KELLOGG_MBA_TUITION = 86370  # Two-Year MBA, year 1 (Kellogg ft-fin-aid 2025-26)
_KELLOGG_MSM_TUITION = 69129  # MiM / MS in Management Studies (10-month program)
_LAW_JD_TUITION = 79772  # $39,886/semester × 2
_LAW_LLM_TUITION = 83462  # General LLM (Chicago Financial Aid COA 2025-26)
_LAW_MSL_TUITION = 65686  # Full-time residential MSL
_FEINBERG_MD_TUITION = 74104
_FEINBERG_MPH_TRIMESTER = 18789
_FEINBERG_MPH_ANNUAL = _FEINBERG_MPH_TRIMESTER * 3  # 56,367
_FEINBERG_MPO_TUITION = 43351
_FEINBERG_PA_TUITION = 57231
_FEINBERG_GC_TRIMESTER = 18519
_FEINBERG_GC_ANNUAL = _FEINBERG_GC_TRIMESTER * 3  # 55,557
_FEINBERG_DPT_TRIMESTER = 18789
_FEINBERG_DPT_ANNUAL = _FEINBERG_DPT_TRIMESTER * 3  # 56,367
_MEDILL_IMC_QUARTER = 20993
_MEDILL_IMC_PROGRAM = _MEDILL_IMC_QUARTER * 4  # 83,972 — 12-month, 4-quarter program
_MEDILL_JOURNALISM_QUARTER = 18368
_MEDILL_JOURNALISM_PROGRAM = _MEDILL_JOURNALISM_QUARTER * 4  # 73,472
_COMM_AUD_QUARTER = 16478
_COMM_AUD_ANNUAL = _COMM_AUD_QUARTER * 3  # 49,434
_COMM_SLP_QUARTER = 19439
_COMM_SLP_ANNUAL = _COMM_SLP_QUARTER * 3  # 58,317
_COMM_RTVF_MFA_QUARTER = 18624
_COMM_RTVF_MFA_ANNUAL = _COMM_RTVF_MFA_QUARTER * 3  # 55,872

# slug → annual tuition_usd (or program total where noted in cost_data.tuition_basis)
_GRAD_TUITION_BY_SLUG: dict[str, int] = {
    "northwestern-mba-ms": _KELLOGG_MBA_TUITION,
    "northwestern-management-sciences-and-quantitative-methods-ms": _KELLOGG_MSM_TUITION,
    "northwestern-master-in-management-ms": _KELLOGG_MSM_TUITION,
    "northwestern-law-prof": _LAW_JD_TUITION,
    "northwestern-llm": _LAW_LLM_TUITION,
    "northwestern-master-science-law-ms": _LAW_MSL_TUITION,
    "northwestern-medicine-prof": _FEINBERG_MD_TUITION,
    "northwestern-public-health-mph": _FEINBERG_MPH_ANNUAL,
    "northwestern-genetic-counseling-ms": _FEINBERG_GC_ANNUAL,
    "northwestern-prosthetics-orthotics-ms": _FEINBERG_MPO_TUITION,
    "northwestern-physician-assistant-ms": _FEINBERG_PA_TUITION,
    "northwestern-physical-therapy-dpt": _FEINBERG_DPT_ANNUAL,
    "northwestern-engineering-management-mem": _MCCORMICK_MEM_ANNUAL,
    "northwestern-creative-writing-mfa": _TGS_MFA_ANNUAL,
    "northwestern-imc-ms": _MEDILL_IMC_PROGRAM,
    "northwestern-journalism-ms": _MEDILL_JOURNALISM_PROGRAM,
    "northwestern-radio-television-and-digital-communication-ms": _COMM_RTVF_MFA_ANNUAL,
    "northwestern-speech-language-pathology-ms": _COMM_SLP_ANNUAL,
    "northwestern-audiology-aud": _COMM_AUD_ANNUAL,
    "northwestern-data-science-ms": 62796,  # 12 courses × $5,098 (SPS MSDS page)
    "northwestern-public-administration-ma": 48276,  # 12 units × $4,023 (SPS per-unit)
    "northwestern-information-systems-ms": 60444,  # 12 units × $5,037
    "northwestern-sports-administration-ma": 52692,  # 12 units × $4,391
    "northwestern-prose-poetry-mfa": 47112,  # 12 units × $3,926
}

# McCormick standard full-time MS (most engineering master's share the SFS rate)
_MCCORMICK_MS_SLUGS = frozenset({
    "northwestern-computer-science-ms",
    "northwestern-machine-learning-data-science-ms",
    "northwestern-artificial-intelligence-ms",
    "northwestern-robotics-ms",
    "northwestern-engineering-design-innovation-ms",
})

# TGS full-time academic-graduate rate (Weinberg / SESP / most TGS master's)
_TGS_MASTERS_SLUGS = frozenset({
    "northwestern-learning-organizational-change-ms",
})


def _grad_cost(spec: dict) -> dict | None:
    """Published graduate/professional cost for a catalog row, or None to omit-with-reason."""
    slug = spec["slug"]
    school = spec["school"]
    dtype = spec.get("degree_type")

    if dtype == "phd":
        return None

    tuition = _GRAD_TUITION_BY_SLUG.get(slug)
    if tuition is None and slug in _MCCORMICK_MS_SLUGS:
        tuition = _MCCORMICK_MS_ANNUAL
    if tuition is None and slug in _TGS_MASTERS_SLUGS:
        tuition = _TGS_MASTERS_ANNUAL

    if tuition is None:
        return None

    # Program-total tuition (online SPS part-time degrees billed per course/unit)
    program_total_slugs = frozenset({
        "northwestern-data-science-ms",
        "northwestern-imc-ms",
        "northwestern-journalism-ms",
        "northwestern-public-administration-ma",
        "northwestern-information-systems-ms",
        "northwestern-sports-administration-ma",
        "northwestern-prose-poetry-mfa",
    })
    tuition_basis = "program" if slug in program_total_slugs else "annual"

    notes: dict[str, str] = {
        "northwestern-mba-ms": (
            "Kellogg Two-Year MBA published tuition for 2025-26 ($86,370 per academic year); "
            "distinct from Northwestern's undergraduate sticker."
        ),
        "northwestern-management-sciences-and-quantitative-methods-ms": (
            "Kellogg MS in Management Studies / MiM published tuition for 2025-26 ($69,129 for "
            "the 10-month program)."
        ),
        "northwestern-master-in-management-ms": (
            "Kellogg Master in Management published tuition for 2025-26 ($69,129 for the "
            "10-month program)."
        ),
        "northwestern-law-prof": (
            "Pritzker Law J.D. tuition for 2025-26 ($39,886 per semester × two semesters = "
            "$79,772)."
        ),
        "northwestern-llm": (
            "Northwestern Pritzker Law General LLM tuition for 2025-26 ($83,462 for the "
            "nine-month program)."
        ),
        "northwestern-master-science-law-ms": (
            "Northwestern Pritzker Law full-time residential MSL tuition for 2025-26 "
            "($65,686)."
        ),
        "northwestern-medicine-prof": (
            "Feinberg MD tuition for 2025-26 ($74,104 per academic year, billed half in "
            "July and half in December)."
        ),
        "northwestern-public-health-mph": (
            "Feinberg MPH full-time tuition for 2025-26 ($18,789 per trimester × three "
            "trimesters)."
        ),
        "northwestern-genetic-counseling-ms": (
            "Feinberg Graduate Program in Genetic Counseling tuition for 2025-26 "
            "($18,519 per trimester × three trimesters)."
        ),
        "northwestern-prosthetics-orthotics-ms": (
            "Feinberg MPO program tuition for 2025-26 ($43,351 per year)."
        ),
        "northwestern-physician-assistant-ms": (
            "Feinberg Physician Assistant program tuition for 2025-26 ($57,231 per year)."
        ),
        "northwestern-physical-therapy-dpt": (
            "Feinberg DPT tuition for 2025-26 ($18,789 per trimester × three trimesters in "
            "years one and two)."
        ),
        "northwestern-engineering-management-mem": (
            "McCormick MEM full-time tuition for 2025-26 ($22,656 per quarter × three "
            "quarters)."
        ),
        "northwestern-creative-writing-mfa": (
            "The Graduate School MFA tuition for 2025-26 ($18,689 per quarter × three "
            "quarters)."
        ),
        "northwestern-imc-ms": (
            "Medill full-time IMC tuition for 2025-26 ($20,993 per quarter × four quarters "
            "in the 12-month program)."
        ),
        "northwestern-journalism-ms": (
            "Medill graduate journalism tuition for 2025-26 ($18,368 per quarter × four "
            "quarters)."
        ),
        "northwestern-radio-television-and-digital-communication-ms": (
            "School of Communication full-time graduate tuition for 2025-26 ($18,624 per "
            "quarter × three quarters)."
        ),
        "northwestern-speech-language-pathology-ms": (
            "School of Communication MSSLL full-time tuition for 2025-26 ($19,439 per "
            "quarter × three quarters)."
        ),
        "northwestern-audiology-aud": (
            "School of Communication AuD full-time tuition for 2025-26 ($16,478 per quarter "
            "× three quarters)."
        ),
        "northwestern-data-science-ms": (
            "SPS online MS in Data Science estimated program tuition for 2025-26 (12 courses "
            "× $5,098 per course = $62,796)."
        ),
        "northwestern-public-administration-ma": (
            "SPS MA in Public Policy & Administration per-unit tuition for 2025-26 ($4,023 × "
            "12 units ≈ $48,276 program total)."
        ),
        "northwestern-information-systems-ms": (
            "SPS MS in Information Systems per-unit tuition for 2025-26 ($5,037 × 12 units "
            "≈ $60,444 program total)."
        ),
        "northwestern-sports-administration-ma": (
            "SPS MA in Sports Administration per-unit tuition for 2025-26 ($4,391 × 12 units "
            "≈ $52,692 program total)."
        ),
        "northwestern-prose-poetry-mfa": (
            "SPS MFA in Prose and Poetry per-unit tuition for 2025-26 ($3,926 × 12 units "
            "≈ $47,112 program total)."
        ),
    }

    default_note = (
        f"McCormick full-time master's tuition for 2025-26 ($22,973 per quarter × three "
        f"quarters = ${_MCCORMICK_MS_ANNUAL:,}), distinct from the undergraduate sticker."
        if slug in _MCCORMICK_MS_SLUGS
        else (
            f"The Graduate School full-time master's tuition for 2025-26 ($22,973 per "
            f"quarter × three quarters = ${_TGS_MASTERS_ANNUAL:,})."
            if slug in _TGS_MASTERS_SLUGS
            else f"Published {school} graduate tuition for 2025-26."
        )
    )

    sources: dict[str, tuple[str, str]] = {
        KELLOGG: (
            "Kellogg School of Management — Tuition & Financial Aid",
            "https://www.kellogg.northwestern.edu/admissions/financial-aid/ft-fin-aid/",
        ),
        LAW: (
            "Northwestern Pritzker School of Law — Tuition Rates",
            "https://www.law.northwestern.edu/admissions/tuitionaid/tuition/",
        ),
        FEINBERG: (
            "Northwestern Student Financial Services — Feinberg School of Medicine",
            f"{_SFS_GRAD}feinberg-school-of-medicine.html",
        ),
        MCCORMICK: (
            "Northwestern Student Financial Services — McCormick School of Engineering",
            f"{_SFS_GRAD}mccormick-school-of-engineering.html",
        ),
        MEDILL: (
            "Northwestern Student Financial Services — Medill School",
            f"{_SFS_GRAD}medill-school-of-journalism.html",
        ),
        COMMUNICATION: (
            "Northwestern Student Financial Services — School of Communication",
            f"{_SFS_GRAD}school-of-communication.html",
        ),
        SPS: (
            "Northwestern Student Financial Services — School of Professional Studies",
            f"{_SFS_GRAD}school-of-professional-studies.html",
        ),
        WEINBERG: (
            "Northwestern Student Financial Services — The Graduate School",
            f"{_SFS_GRAD}the-graduate-school.html",
        ),
        SESP: (
            "Northwestern Student Financial Services — The Graduate School",
            f"{_SFS_GRAD}the-graduate-school.html",
        ),
    }
    src_label, src_url = sources.get(
        school,
        (
            "Northwestern Student Financial Services — Graduate Tuition",
            _SFS_GRAD,
        ),
    )

    return {
        "tuition_usd": tuition,
        "tuition_basis": tuition_basis,
        "funded": False,
        "note": notes.get(slug, default_note),
        "source": src_label,
        "source_url": src_url,
        "year": "2025-26",
    }

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Application (Common Application or Coalition Application)", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$75 application fee (fee waivers available)", "required": True},
        {
            "name": "SAT/ACT scores",
            "required": False,
            "note": "Northwestern is test-optional; the middle 50% of enrolled students who submitted scored SAT 1510–1560 / ACT 34–35 (CDS 2024-25).",
        },
    ],
    "deadlines": [
        {"round": "Early Decision I", "date": "November 1"},
        {"round": "Early Decision II", "date": "January 2"},
        {"round": "Regular Decision", "date": "January 2"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": {
            "types": ["F-1", "J-1"],
            "note": "International students receive an I-20 after admission.",
        },
        "sources": [
            {
                "label": "Northwestern Undergraduate Admissions",
                "url": "https://admissions.northwestern.edu/apply/",
            }
        ],
    },
    "source": "Northwestern Undergraduate Admissions",
    "source_url": "https://admissions.northwestern.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Northwestern graduate application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most Northwestern graduate programs require two or three letters; check the program's page.",
        },
        {
            "name": "GRE/GMAT scores",
            "required": False,
            "note": "Test requirements vary by program; many Northwestern graduate programs are test-optional.",
        },
    ],
    "deadlines": [
        {
            "round": "Fall admission",
            "date": "Deadlines vary by program (typically December–January)",
        }
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": "Required for applicants whose native language is not English.",
        },
        "visa": {
            "types": ["F-1", "J-1"],
            "note": "International students receive an I-20 after admission.",
        },
        "sources": [
            {
                "label": "The Graduate School — Admissions",
                "url": "https://www.tgs.northwestern.edu/admission/",
            }
        ],
    },
    "source": "The Graduate School — Admissions",
    "source_url": "https://www.tgs.northwestern.edu/admission/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 89363,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 147767)",
    "source_url": "https://collegescorecard.ed.gov/school/?147767-Northwestern-University",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "northwestern-computer-science-bs": {
        "summary": (
            "Northwestern's undergraduate computer science program combines McCormick engineering "
            "rigor with strong ties to AI, data science, and interdisciplinary research through "
            "NICO and the CS+X joint majors. Students praise small upper-level classes and Chicago "
            "tech recruiting access, though the core is theory-heavy and some wish for more "
            "industry-facing project courses than peer programs offer."
        ),
        "themes": [
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": "CS+X majors and NICO partnerships connect computing to journalism, music, and design.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; fewer applied-software electives than some peers.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in AI, HCI, and computational social science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates land at major tech firms, startups, and PhD programs nationwide.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Northwestern University",
                "url": "https://www.niche.com/colleges/northwestern-university/",
            },
            {
                "label": "U.S. News — Best Undergraduate Computer Science Programs",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-economics-bs": {
        "summary": (
            "Economics is one of the largest majors at Weinberg, known for rigorous quantitative "
            "training and a path to consulting, finance, and graduate school. Students appreciate "
            "the math-heavy curriculum and faculty research access, though introductory courses can "
            "be large and competitive grading is common."
        ),
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Math-intensive core prepares students for grad school and analytics roles.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join faculty labs in applied micro, macro, and econometrics.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "mixed",
                "detail": "Popular major means big lectures in introductory sequences.",
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": "Strong placement in consulting, finance, and PhD programs.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Northwestern University",
                "url": "https://www.niche.com/colleges/northwestern-university/",
            },
            {
                "label": "Weinberg — Department of Economics",
                "url": "https://economics.northwestern.edu/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-mba-ms": {
        "summary": (
            "Kellogg's full-time MBA is a top-tier program known for its collaborative culture, "
            "marketing strength, and Chicago finance and consulting pipelines. Reviewers highlight "
            "team-based learning and strong alumni network, though the quarter system is fast-paced "
            "and tuition is among the highest nationally."
        ),
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning and a non-cutthroat cohort culture are program hallmarks.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among the top marketing MBA programs.",
            },
            {
                "label": "Fast pace",
                "sentiment": "caution",
                "detail": "The quarter system compresses coursework; time management is essential.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared to some peers.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Kellogg School of Management",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
            {
                "label": "U.S. News — Best Business Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/northwestern-university-01027",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-law-prof": {
        "summary": (
            "Northwestern Pritzker Law is a top-20 law school known for its accelerated J.D. option, "
            "strong clinical programs through the Bluhm Legal Clinic, and Chicago legal market "
            "placement. Students praise practical training and faculty access, though the workload "
            "is intense and Big Law placement is competitive at the very top firms."
        ),
        "themes": [
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Bluhm Legal Clinic offers extensive hands-on litigation and advocacy experience.",
            },
            {
                "label": "Chicago placement",
                "sentiment": "positive",
                "detail": "Strong pipelines to Chicago Big Law, corporate counsel, and federal clerkships.",
            },
            {
                "label": "Accelerated option",
                "sentiment": "positive",
                "detail": "Two-year J.D. track attracts experienced professionals and career changers.",
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": "Quarter system and competitive grading demand strong time management.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Law Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/northwestern-university-03058",
            },
            {
                "label": "Pritzker School of Law — About",
                "url": "https://www.law.northwestern.edu/about/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-medicine-prof": {
        "summary": (
            "Feinberg School of Medicine is a top research medical school affiliated with "
            "Northwestern Memorial Hospital, known for its Health & Society curriculum and strong "
            "NIH-funded research. Admission is extraordinarily competitive and the environment is "
            "demanding, though Chicago clinical exposure is exceptional."
        ),
        "themes": [
            {
                "label": "Research excellence",
                "sentiment": "positive",
                "detail": "Feinberg ranks among the top NIH-funded medical schools nationally.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Northwestern Memorial and affiliated hospitals provide diverse patient-care exposure.",
            },
            {
                "label": "Extreme selectivity",
                "sentiment": "caution",
                "detail": "Acceptance rate below 3% with exceptional MCAT/GPA profiles expected.",
            },
            {
                "label": "Demanding environment",
                "sentiment": "mixed",
                "detail": "High expectations and workload; support systems exist but stress is real.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Medical Schools: Research",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-040101",
            },
            {
                "label": "Feinberg School of Medicine — About",
                "url": "https://www.feinberg.northwestern.edu/about/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-journalism-bs": {
        "summary": (
            "Medill's undergraduate journalism program is among the most respected in the country, "
            "combining reporting fundamentals with digital and data journalism through the Knight "
            "Lab. Students praise faculty practitioners and Chicago media access, though the "
            "industry's contraction makes career planning essential early."
        ),
        "themes": [
            {
                "label": "Industry reputation",
                "sentiment": "positive",
                "detail": "Medill is perennially ranked among the top journalism schools nationally.",
            },
            {
                "label": "Digital innovation",
                "sentiment": "positive",
                "detail": "Knight Lab and data-journalism courses keep the curriculum current.",
            },
            {
                "label": "Practitioner faculty",
                "sentiment": "positive",
                "detail": "Working journalists and editors teach core reporting courses.",
            },
            {
                "label": "Industry headwinds",
                "sentiment": "caution",
                "detail": "Traditional newsroom jobs are scarce; students must build versatile skill sets.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Undergraduate Journalism Programs",
                "url": "https://www.usnews.com/best-colleges/rankings/journalism",
            },
            {
                "label": "Medill — Undergraduate Journalism",
                "url": "https://www.medill.northwestern.edu/journalism/undergraduate/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-biomedical-medical-engineering-bs": {
        "summary": (
            "Northwestern's biomedical engineering major combines McCormick engineering with "
            "Feinberg Medicine proximity and strong bioelectronics research. Students highlight "
            "interdisciplinary labs and pre-med flexibility, though the workload is intense and "
            "course sequencing requires careful planning."
        ),
        "themes": [
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "Querrey Simpson Institute for Bioelectronics and Feinberg partnerships enrich the major.",
            },
            {
                "label": "Pre-med pathway",
                "sentiment": "positive",
                "detail": "Many BME graduates pursue medical school or industry med-device roles.",
            },
            {
                "label": "Heavy workload",
                "sentiment": "caution",
                "detail": "Engineering core plus biology prerequisites demand strong time management.",
            },
            {
                "label": "Graduate outcomes",
                "sentiment": "positive",
                "detail": "Strong placement in med school, biotech, and PhD programs.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Undergraduate Biomedical Engineering Programs",
                "url": "https://www.usnews.com/best-colleges/rankings/biological-engineering-overall",
            },
            {
                "label": "McCormick — Biomedical Engineering",
                "url": "https://www.mccormick.northwestern.edu/biomedical/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-psychology-general-bs": {
        "summary": (
            "Psychology is one of Weinberg's most popular majors, offering research opportunities "
            "in clinical, cognitive, and social psychology. Students value faculty labs and the "
            "path to graduate study, though large introductory sections and competitive research "
            "assistant placements are common."
        ),
        "themes": [
            {
                "label": "Research opportunities",
                "sentiment": "positive",
                "detail": "Undergraduates join faculty labs across clinical, cognitive, and social areas.",
            },
            {
                "label": "Graduate preparation",
                "sentiment": "positive",
                "detail": "Strong track record for PhD and clinical psychology program admission.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "mixed",
                "detail": "High enrollment means big lectures in introductory psychology sequences.",
            },
            {
                "label": "Competitive RA spots",
                "sentiment": "caution",
                "detail": "Research assistant positions are sought-after and require early outreach.",
            },
        ],
        "sources": [
            {
                "label": "Niche — Northwestern University",
                "url": "https://www.niche.com/colleges/northwestern-university/",
            },
            {
                "label": "Weinberg — Department of Psychology",
                "url": "https://psychology.northwestern.edu/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-radio-television-and-digital-communication-ms": {
        "summary": (
            "The School of Communication's RTVF graduate program is a respected pipeline to film, "
            "television, and digital media production, with strong ties to Chicago and Los Angeles "
            "industry networks. Students praise hands-on production training, though funding is "
            "limited and career outcomes vary by concentration."
        ),
        "themes": [
            {
                "label": "Production training",
                "sentiment": "positive",
                "detail": "Hands-on film, TV, and digital media production courses are program strengths.",
            },
            {
                "label": "Industry networks",
                "sentiment": "positive",
                "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms.",
            },
            {
                "label": "Limited funding",
                "sentiment": "caution",
                "detail": "Graduate funding is scarcer than in STEM PhD programs.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend heavily on portfolio quality and industry connections.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Fine Arts Programs",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058",
            },
            {
                "label": "School of Communication — RTVF",
                "url": "https://communication.northwestern.edu/departments/rtvf/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-management-sciences-and-quantitative-methods-ms": {
        "summary": (
            "Kellogg's MS in Management Studies and analytics-oriented graduate offerings attract "
            "students seeking quantitative business training without a full MBA timeline. Reviewers "
            "note strong analytics curriculum and Kellogg brand access, though the program is newer "
            "than dedicated M.S. in Business Analytics peers and career services are MBA-centric."
        ),
        "themes": [
            {
                "label": "Quantitative curriculum",
                "sentiment": "positive",
                "detail": "Analytics, statistics, and decision-science courses anchor the program.",
            },
            {
                "label": "Kellogg brand",
                "sentiment": "positive",
                "detail": "Access to Kellogg recruiting events and alumni network.",
            },
            {
                "label": "Program maturity",
                "sentiment": "mixed",
                "detail": "Younger than dedicated MSBA programs at MIT Sloan or USC Marshall.",
            },
            {
                "label": "MBA-centric services",
                "sentiment": "caution",
                "detail": "Career services are primarily oriented toward full-time MBA students.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Kellogg School of Management",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
            {
                "label": "Kellogg — MS in Management Studies",
                "url": "https://www.kellogg.northwestern.edu/programs/msms.aspx",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "northwestern-radio-television-and-digital-communication-bs": {
        "summary": (
            "Northwestern's undergraduate RTVF program is one of the nation's most respected film and "
            "television pipelines, with hands-on production training and strong Chicago and Los Angeles "
            "industry connections. Students praise the creative community and portfolio-building "
            "opportunities, though equipment access can be competitive and career outcomes vary by concentration."
        ),
        "themes": [
            {
                "label": "Production training",
                "sentiment": "positive",
                "detail": "Hands-on film, TV, and digital media courses anchor the undergraduate curriculum.",
            },
            {
                "label": "Industry pipelines",
                "sentiment": "positive",
                "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms.",
            },
            {
                "label": "Creative community",
                "sentiment": "positive",
                "detail": "Collaborative cohort culture supports portfolio development and peer filmmaking.",
            },
            {
                "label": "Resource competition",
                "sentiment": "mixed",
                "detail": "Studio equipment and editing suites are sought-after among production students.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Fine Arts Programs",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058",
            },
            {
                "label": "School of Communication — RTVF",
                "url": "https://communication.northwestern.edu/departments/rtvf/",
            },
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
}

_FLAGSHIP = "northwestern-mba-ms"
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "northwestern-computer-science-bs": ["computer science", "CS", "McCormick"],
    "northwestern-economics-bs": ["economics", "Weinberg"],
    "northwestern-mba-ms": ["MBA", "Kellogg"],
    "northwestern-law-prof": ["JD", "Pritzker School of Law"],
    "northwestern-medicine-prof": ["MD", "Feinberg", "medicine"],
    "northwestern-journalism-bs": ["journalism", "Medill"],
    "northwestern-biomedical-medical-engineering-bs": ["biomedical engineering", "BME"],
    "northwestern-psychology-general-bs": ["psychology", "Weinberg"],
    "northwestern-radio-television-and-digital-communication-ms": ["RTVF", "film", "television"],
    "northwestern-management-sciences-and-quantitative-methods-ms": [
        "MSMS",
        "analytics",
        "Kellogg",
    ],
}


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "outcomes_data.conditions",
    ]
    if spec.get("degree_type") not in ("bachelors", "phd") and slug not in _COST_BY_SLUG:
        if _grad_cost(spec) is None:
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


def _requirements_for(spec: dict) -> dict:
    return dict(_REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else _REQ_GRAD)


def _website_for(spec: dict) -> str:
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.northwestern.edu/")


def apply(session: Session) -> bool:
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            school_outcomes.pop(_path.split(".", 1)[1], None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1851
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.northwestern.edu"
    hero = SCHOOL_OUTCOMES["campus_photos"][0]["url"]
    _gallery = [u for u in (inst.media_gallery or []) if u != hero]
    inst.media_gallery = [hero, *_gallery]
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
        sc.website_url = SCHOOL_WEBSITE.get(spec["name"])
        m = next(x for x in _SCHOOL_META if x["name"] == spec["name"])
        about = dict(_about_for(m))
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
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'programs' AND ccu.column_name = 'id' AND tc.table_name <> 'programs'
    """)
    ).fetchall()
    for table, col in fks:
        if session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}
        ).first():
            return True
    return False


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
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = _website_for(spec)
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "on_campus")
        p.department = spec.get("department")
        # Matcher-core CIP join key + universal program-DISTINCT who_its_for depth field
        # (REPAIR_BACKLOG #1 + #4). cip_code is the verified IPEDS CIP family code on the
        # spec; who_its_for is the field-specific audience statement (never a type template,
        # never None — the build gate above asserts coverage + distinctness ≥ 0.9).
        p.cip_code = spec.get("cip")
        p.who_its_for = WHO_BY_SLUG.get(slug) or _who_for(spec)
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        if spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UG
            p.cost_data = {
                "tuition_usd": _TUITION_UG,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "funded": False,
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2024-25",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0,
                "funded": True,
                "note": "Northwestern PhD students typically receive full tuition plus a stipend.",
                "source": "The Graduate School — Funding",
                "source_url": "https://www.tgs.northwestern.edu/funding/",
            }
        elif (grad_cost := _grad_cost(spec)) is not None:
            p.tuition = grad_cost.get("tuition_usd")
            p.cost_data = dict(grad_cost)
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "Northwestern program tuition page",
                "source_url": _website_for(spec),
            }
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
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
