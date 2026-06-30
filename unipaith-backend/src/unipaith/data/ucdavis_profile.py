"""University of California, Davis — gold-standard profile (institution + schools + catalog).

Every value below is verified against an authoritative source (UC Davis's official pages —
ucdavis.edu, catalog.ucdavis.edu, the colleges' and professional schools' sites, the UC
Office of the President 2025-26 systemwide Tuition & Fee Levels table [ucop.edu], the U.S.
Dept. of Education College Scorecard / NCES College Navigator for UNITID 110644, and the
ranking bodies) and carries a citation, or is honestly omitted (recorded in that node's
``_standard.omitted``) — never guessed.

Scope note: UC Davis entered as a 5-stub institution seed (the 2026-06 US-News bulk seed)
whose five programs ALL shipped with an EMPTY ``description_text`` and a NULL ``department``
— a blank student page and zero matcher embedding (REPAIR_BACKLOG run 86 entry #2, the
worst open defect tier; the sibling UVA and WashU seeds were cleared earlier this cycle).
This pass (2026-06-26) takes the institution to gold (filling the seed's missing
report-card / admissions-funnel / diversity / cost-aid / campus-resources / rankings /
campus-photo-gallery / feed fields) and REPLACES the five empty stubs with a verified,
real-named catalog across UC Davis's degree-granting colleges and schools — the College of
Agricultural and Environmental Sciences, the College of Biological Sciences, the College of
Engineering, the College of Letters and Science, the Graduate School of Management, the
School of Education, the School of Law, the School of Medicine, the UC Davis Weill School of
Veterinary Medicine, the Betty Irene Moore School of Nursing, and Graduate Studies.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean,
gold contrast), a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``
(from the IPEDS/Scorecard CIP families for UNITID 110644), a verified ``delivery_format``,
published tuition per credential level, working UC Davis news feeds, and sourced
``external_reviews`` on the obviously-coverable flagships (the #1-ranked D.V.M., the M.D.,
the J.D., and the Graduate School of Management M.B.A.). Nothing is padded.

Public-university tuition (run-83 rule): UC Davis publishes TWO undergraduate stickers — a
California-resident rate and a much higher non-resident rate. The CPEF matcher reads the
flat ``program.tuition`` scalar for its budget veto, so the scalar carries the NON-RESIDENT
(out-of-state) figure — the conservative, broadly-correct input for a national/international
applicant pool — while ``cost_data.breakdown`` preserves BOTH rates. Undergraduate
tuition+fees: $16,774 (CA) / $50,974 (non-CA), IPEDS 2024-25 (UNITID 110644). Academic
master's carry the UC systemwide non-resident graduate-academic tuition + Student Services
Fee ($29,532, UCOP 2025-26; campus-based fees additional). Professional degrees carry each
school's published non-resident tuition + fees where one could be verified (J.D. $72,115;
M.D. $60,525; D.V.M. $42,695; LL.M. $65,879; full-time M.B.A. $63,542; M.P.H. $42,205 — the
last two read off each program's own published tuition page, resident + non-resident in the
breakdown). The remaining professional master's whose exact all-in tuition+fees could not be
isolated from a published page this session (the M.P.V.M., the nursing master's, the Ed.D.)
record the verified UCOP Professional Degree Supplemental Tuition in an omit-with-reason note
rather than a guessed total. Funded research doctorates carry
funded=True / tuition=None (UC research Ph.D.s are supported by fellowship/TA/GSR
appointments with fee remission).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of California-Davis"

ENRICHED_AT = "2026-06-30"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # UC Davis is test-blind: SAT/ACT scores are not used in admission or scholarship
    # decisions, so there is no enrolled-student test-score range to report (omitted, not
    # guessed).
    "school_outcomes.test_scores",
    # UC Davis publishes a student-faculty ratio but not a single current
    # instructional-faculty headcount that could be verified this session.
    "school_outcomes.scale.faculty_count",
    # Career outcomes are published per-college/per-school rather than as one
    # institution-wide employed-or-continuing-education figure; median earnings are provided.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "public",
    # WASC Senior College and University Commission (UC Davis's regional accreditor).
    "accreditor": "WSCUC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {"rank": 114, "year": 2026},
    # Times Higher Education World University Rankings 2026.
    "times_higher_education": {"rank": 64, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #32 nationally (tie),
    # #9 among public universities.
    "us_news_national": {"rank": 32, "year": 2026},
}

# ── Verified campus-photo gallery (Wikimedia Commons; each credit verified via the
#    Commons extmetadata Artist + LicenseShortName; the seed shipped only 3 photos, below
#    the >=4 gold gallery gate, so the full verified gallery is set here). ──
_CAMPUS_PHOTOS: list[dict] = [
    {
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/"
            "UC_Davis_Memorial_Union.jpg/1920px-UC_Davis_Memorial_Union.jpg"
        ),
        "credit": "Wikimedia Commons / Borawik (CC BY-SA 4.0)",
    },
    {
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/"
            "Manetti_Shrem_Museum_of_Art_swirling_canopies.jpg/"
            "1920px-Manetti_Shrem_Museum_of_Art_swirling_canopies.jpg"
        ),
        "credit": "Wikimedia Commons / Cullen328 (CC BY-SA 3.0)",
    },
    {
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/"
            "UC_Davis_campus_buildings_and_scenes_%2816188061937%29.jpg/"
            "1920px-UC_Davis_campus_buildings_and_scenes_%2816188061937%29.jpg"
        ),
        "credit": "Wikimedia Commons / UC Davis Arboretum and Public Garden (CC BY 2.0)",
    },
    {
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/"
            "Cycling_On_Campus.jpg/1920px-Cycling_On_Campus.jpg"
        ),
        "credit": "Wikimedia Commons / UC Davis College of Engineering (CC BY 2.0)",
    },
    {
        "url": (
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/"
            "Manetti_Shrem_Museum_of_Art.jpg/1920px-Manetti_Shrem_Museum_of_Art.jpg"
        ),
        "credit": "Wikimedia Commons / Cullen328 (CC BY-SA 3.0)",
    },
]

SCHOOL_OUTCOMES: dict = {
    # NCES College Navigator / College Scorecard (UNITID 110644), Fall 2024 funnel.
    "admit_rate": 0.42,
    "avg_net_price": 14741,
    "median_earnings_10yr": 80838,
    # IPEDS — six-year graduation rate (Fall 2018 cohort).
    "graduation_rate_6yr": 0.86,
    # IPEDS — first-year retention (Fall 2023 → Fall 2024 full-time).
    "retention_rate_first_year": 0.93,
    # Undergraduate race/ethnicity (U.S. Dept. of Education College Scorecard, UNITID
    # 110644). UC Davis is a federally designated Hispanic-Serving Institution and an
    # Asian American and Native American Pacific Islander-Serving Institution. Categories
    # plus other/unreported make up the remainder, so shares do not sum to 100%.
    "demographics": {
        "asian": 0.313,
        "hispanic": 0.246,
        "white": 0.205,
        "note": (
            "Undergraduate race/ethnicity (U.S. Dept. of Education College Scorecard). "
            "UC Davis is a Hispanic-Serving Institution; the remaining categories "
            "(Black, international, two-or-more, and unreported) are not all individually "
            "shown here, so the shares do not sum to 100%."
        ),
        "source": "U.S. Dept. of Education College Scorecard — UC Davis (UNITID 110644)",
        "source_url": "https://collegescorecard.ed.gov/school/?110644",
    },
    "financial_aid": {
        # College Scorecard — share of undergraduates receiving Pell grants.
        "pell_grant_rate": 0.308,
        # UC Davis Financial Aid — 2025-26 estimated non-resident cost of attendance
        # (tuition + fees + housing + food + books + personal + transportation).
        "cost_of_attendance": 84400,
        "source": "UC Davis — Cost of Attendance (2025-26)",
        "source_url": "https://www.ucdavis.edu/admissions/cost",
    },
    "research": {
        "labs": [
            "UC Davis Comprehensive Cancer Center",
            "UC Davis MIND Institute",
            "UC Davis Health",
            "Bodega Marine Laboratory",
            "UC Davis Library",
        ],
        "areas": [
            "Agriculture, food & the environment",
            "Veterinary, animal & comparative biology",
            "Human & planetary health",
            "Neuroscience & neurodevelopment",
            "Energy, transportation & sustainability",
            "Plant sciences & viticulture",
        ],
        "lab_links": {
            "UC Davis Comprehensive Cancer Center": "https://health.ucdavis.edu/cancer/",
            "UC Davis MIND Institute": "https://health.ucdavis.edu/mind-institute/",
            "UC Davis Library": "https://library.ucdavis.edu/",
        },
        "source": "UC Davis — Research",
        "source_url": "https://research.ucdavis.edu/",
    },
    "scale": {
        # NCES College Navigator (Fall 2024) total + undergraduate enrollment.
        "total_enrollment": 40065,
        "undergraduate_enrollment": 32273,
        "student_faculty_ratio": "22:1",
        "research_centers": [
            "UC Davis Comprehensive Cancer Center",
            "UC Davis MIND Institute",
            "Bodega Marine Laboratory",
        ],
    },
    "campus_life": {
        # The Aggies compete in NCAA Division I; most sports join the Mountain West
        # Conference effective July 2026, with football in the Big Sky Conference (FCS).
        "athletics_division": (
            "NCAA Division I (Mountain West Conference, effective July 2026; "
            "football in the Big Sky Conference)"
        ),
        "mascot": "UC Davis Aggies",
        "housing": "Residential campus in Davis, California",
        "resources": [
            {"label": "UC Davis Aggies Athletics", "url": "https://ucdavisaggies.com/"},
            {"label": "UC Davis Library", "url": "https://library.ucdavis.edu/"},
            {
                "label": "Manetti Shrem Museum of Art",
                "url": "https://manettishremmuseum.ucdavis.edu/",
            },
            {
                "label": "UC Davis Internship & Career Center",
                "url": "https://careercenter.ucdavis.edu/",
            },
        ],
    },
    "campus_photos": _CAMPUS_PHOTOS,
    "media_credit": _CAMPUS_PHOTOS[0]["credit"],
    # UC Davis main campus (Davis, California).
    "location": {"lat": 38.5382, "lng": -121.7617},
    "flagship": {
        "enrollment_total": 40065,
        # First-year admissions funnel (NCES College Navigator, Fall 2024).
        "applicants": 98864,
        "admits": 41523,
        "admissions_cycle": "Fall 2024 first-year (NCES College Navigator / IPEDS)",
        "founded_year": 1905,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UC Davis, UNITID 110644)",
            "url": "https://collegescorecard.ed.gov/school/?110644",
        },
        {
            "label": "NCES College Navigator — University of California-Davis (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=110644",
        },
        {
            "label": "UC Office of the President — 2025-26 Tuition & Fee Levels",
            "url": "https://www.ucop.edu/operating-budget/_files/fees/202526/2025-26.pdf",
        },
        {
            "label": "UC Davis — Cost of Attendance",
            "url": "https://www.ucdavis.edu/admissions/cost",
        },
        {
            "label": "QS World University Rankings 2026 — UC Davis",
            "url": "https://www.topuniversities.com/universities/university-california-davis",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — UC Davis",
            "url": (
                "https://www.timeshighereducation.com/world-university-rankings/"
                "university-california-davis"
            ),
        },
        {
            "label": "U.S. News Best Colleges 2026 — UC Davis",
            "url": "https://www.usnews.com/best-colleges/university-of-california-davis-1313",
        },
    ],
}

UNDERGRAD_COUNT = 32273

DESCRIPTION = (
    "The University of California, Davis is a public research university in Davis, "
    "California, founded in 1905 as the University Farm and now the largest UC campus by "
    "land area. A member of the Association of American Universities, it enrolls about "
    "32,300 undergraduates and some 7,800 graduate and professional students — roughly "
    "40,000 in all — with a 22:1 student-faculty ratio, and is classified as a Carnegie "
    "R1 very-high-research-activity university.\n\n"
    "UC Davis is organized into four undergraduate colleges and a set of graduate and "
    "professional schools: the College of Agricultural and Environmental Sciences, the "
    "College of Biological Sciences, the College of Engineering, and the College of "
    "Letters and Science, alongside the Graduate School of Management, the School of "
    "Education, the School of Law, the School of Medicine, the UC Davis Weill School of "
    "Veterinary Medicine, the Betty Irene Moore School of Nursing, and Graduate Studies. "
    "Its School of Veterinary Medicine is ranked No. 1 in the United States.\n\n"
    "Accredited by WSCUC, UC Davis ranks among the top public universities in the country "
    "— No. 32 nationally (No. 9 among publics) by U.S. News, No. 64 in the world by Times "
    "Higher Education, and No. 114 by QS. It admitted about 42% of first-year applicants "
    "for fall 2024, graduates about 86% of its undergraduates within six years, and is "
    "test-blind, using neither the SAT nor the ACT in admission decisions.\n\n"
    "UC Davis's published 2024-25 undergraduate tuition and fees are $16,774 for "
    "California residents and $50,974 for non-residents, with an average net price of "
    "about $14,700 after aid. Its teams, the Aggies, compete in NCAA Division I."
)

# ── The real degree-granting colleges & schools (display order) ────────────
_CAES = "College of Agricultural and Environmental Sciences"
_CBS = "College of Biological Sciences"
_COE = "College of Engineering"
_LS = "College of Letters and Science"
_GSM = "Graduate School of Management"
_EDU = "School of Education"
_LAW = "School of Law"
_MED = "School of Medicine"
_VET = "UC Davis Weill School of Veterinary Medicine"
_NURS = "The Betty Irene Moore School of Nursing"
_GRAD = "Graduate Studies"

_SCHOOL_WEBSITE: dict[str, str] = {
    _CAES: "https://caes.ucdavis.edu/",
    _CBS: "https://biology.ucdavis.edu/",
    _COE: "https://engineering.ucdavis.edu/",
    _LS: "https://ls.ucdavis.edu/",
    _GSM: "https://gsm.ucdavis.edu/",
    _EDU: "https://education.ucdavis.edu/",
    _LAW: "https://law.ucdavis.edu/",
    _MED: "https://health.ucdavis.edu/medschool/",
    _VET: "https://www.vetmed.ucdavis.edu/",
    _NURS: "https://health.ucdavis.edu/nursing/",
    _GRAD: "https://grad.ucdavis.edu/",
}

SCHOOLS: list[dict] = [
    {
        "name": _CAES,
        "sort_order": 1,
        "description": (
            "UC Davis's founding college, the College of Agricultural and Environmental "
            "Sciences spans the agricultural, environmental, human, and social sciences — "
            "from animal and plant sciences and food science to environmental policy, "
            "nutrition, human development, and agricultural economics — and anchors the "
            "university's land-grant research mission."
        ),
    },
    {
        "name": _CBS,
        "sort_order": 2,
        "description": (
            "The College of Biological Sciences teaches and researches life from molecules "
            "to ecosystems across its departments of molecular and cellular biology, "
            "microbiology and molecular genetics, evolution and ecology, plant biology, and "
            "neurobiology, physiology and behavior."
        ),
    },
    {
        "name": _COE,
        "sort_order": 3,
        "description": (
            "The College of Engineering educates engineers across aerospace, biomedical, "
            "chemical, civil and environmental, computer, electrical, materials, and "
            "mechanical engineering, with strengths in transportation, energy, and "
            "agricultural and biological systems engineering."
        ),
    },
    {
        "name": _LS,
        "sort_order": 4,
        "description": (
            "The College of Letters and Science is UC Davis's largest college, spanning the "
            "humanities, arts, social sciences, and the physical and mathematical sciences "
            "— from English, history, and the languages to economics, psychology, "
            "chemistry, physics, mathematics, and statistics."
        ),
    },
    {
        "name": _GSM,
        "sort_order": 5,
        "description": (
            "The Graduate School of Management offers the M.B.A. and specialized business "
            "master's degrees, pairing analytical management education with UC Davis's "
            "strengths in technology, agriculture, food, and sustainability."
        ),
    },
    {
        "name": _EDU,
        "sort_order": 6,
        "description": (
            "The School of Education prepares teachers and education leaders and conducts "
            "research on learning, equity, and policy, offering teaching credentials, the "
            "Ph.D. in education, and the CANDEL Ed.D. for working leaders."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 7,
        "description": (
            "UC Davis School of Law (King Hall) is a public law school known for its "
            "collegial culture and strengths in public-interest, environmental, and "
            "immigration law, offering the J.D. and the LL.M."
        ),
    },
    {
        "name": _MED,
        "sort_order": 8,
        "description": (
            "The School of Medicine educates physicians and biomedical scientists and, "
            "through UC Davis Health, runs an academic medical center, an NCI-designated "
            "comprehensive cancer center, and the MIND Institute for neurodevelopment."
        ),
    },
    {
        "name": _VET,
        "sort_order": 9,
        "description": (
            "The UC Davis Weill School of Veterinary Medicine is ranked No. 1 in the United "
            "States and among the best in the world. It awards the D.V.M. and graduate "
            "degrees and runs one of the largest veterinary teaching hospitals anywhere, "
            "spanning companion-animal, livestock, wildlife, and One Health research."
        ),
    },
    {
        "name": _NURS,
        "sort_order": 10,
        "description": (
            "The Betty Irene Moore School of Nursing educates nurses and nurse leaders "
            "through its master's-entry program, family nurse practitioner and nurse "
            "anesthesia doctorates, and a Ph.D. in nursing science and health-care "
            "leadership."
        ),
    },
    {
        "name": _GRAD,
        "sort_order": 11,
        "description": (
            "Graduate Studies administers UC Davis's master's and doctoral programs, many "
            "organized as interdisciplinary graduate groups that draw faculty from across "
            "the colleges and schools."
        ),
    },
]

# ── Feeds (both verified to fetch live items) ──────────────────────────────
# Institution-wide news feed (verified: returns >=10 <item> entries).
_UCD_NEWS_RSS = "https://www.ucdavis.edu/news/all/feed"
_UCD_NEWS_URL = "https://www.ucdavis.edu/news"
# UC Davis Health feed (verified: returns ~30 <item> entries) — used by the health-system
# schools (Medicine, Nursing, Veterinary Medicine).
_UCD_HEALTH_RSS = "https://health.ucdavis.edu/news/rss"
_UCD_HEALTH_URL = "https://health.ucdavis.edu/news/"

_SCHOOL_OWN_FEED: dict[str, str] = {
    _MED: _UCD_HEALTH_RSS,
    _NURS: _UCD_HEALTH_RSS,
    _VET: _UCD_HEALTH_RSS,
}
_SCHOOL_OWN_FEED_URL: dict[str, str] = {
    _MED: _UCD_HEALTH_URL,
    _NURS: _UCD_HEALTH_URL,
    _VET: _UCD_HEALTH_URL,
}

_SOCIAL_UCD = {
    "instagram": "https://www.instagram.com/ucdavis/",
    "linkedin": "https://www.linkedin.com/school/uc-davis/",
    "x": "https://x.com/ucdavis",
    "youtube": "https://www.youtube.com/user/UCDavis",
    "facebook": "https://www.facebook.com/UCDavis",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _UCD_NEWS_RSS,
    "news_url": _UCD_NEWS_URL,
    "news_curated": False,
    "social": dict(_SOCIAL_UCD),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _CAES: ["Agricultural and Environmental Sciences", "CA&ES", "agriculture", "environment"],
    _CBS: ["Biological Sciences", "biology", "life sciences", "research"],
    _COE: ["Engineering", "UC Davis Engineering", "technology"],
    _LS: ["Letters and Science", "humanities", "social sciences", "physical sciences"],
    _GSM: ["Graduate School of Management", "MBA", "business"],
    _EDU: ["School of Education", "teaching", "education"],
    _LAW: ["School of Law", "King Hall", "legal"],
    _MED: ["School of Medicine", "UC Davis Health", "medical"],
    _VET: ["Veterinary Medicine", "School of Veterinary Medicine", "veterinary"],
    _NURS: ["School of Nursing", "Betty Irene Moore", "nursing"],
    _GRAD: ["graduate", "Ph.D.", "research", "graduate group"],
}


def _school_content(name: str) -> dict:
    """A school's content_sources: its own working feed when it has one (the health-system
    schools use the UC Davis Health feed), else the institution feed, filtered by
    school-naming keywords."""
    feed = _SCHOOL_OWN_FEED.get(name, _UCD_NEWS_RSS)
    url = _SCHOOL_OWN_FEED_URL.get(name) or _SCHOOL_WEBSITE.get(name, _UCD_NEWS_URL)
    return {
        "news_rss": feed,
        "news_url": url,
        "news_curated": False,
        "keywords": list(_SCHOOL_KEYWORDS.get(name, [])),
        "social": dict(_SOCIAL_UCD),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    feed = _SCHOOL_OWN_FEED.get(school_name, _UCD_NEWS_RSS)
    url = _SCHOOL_OWN_FEED_URL.get(school_name) or _SCHOOL_WEBSITE.get(school_name, _UCD_NEWS_URL)
    return {
        "news_rss": feed,
        "news_url": url,
        "news_curated": False,
        "keywords": list(keywords),
        "social": dict(_SOCIAL_UCD),
    }


# ── About-detail per school (founded / focus) ──────────────────────────────
_ABOUT_DETAIL: dict[str, dict] = {
    _CAES: {
        "focus": "Agricultural, environmental, human, and social sciences — UC Davis's "
        "founding land-grant college.",
        "source_url": "https://caes.ucdavis.edu/",
    },
    _CBS: {
        "focus": "Biology from molecules to ecosystems across five life-science departments.",
        "source_url": "https://biology.ucdavis.edu/",
    },
    _COE: {
        "focus": "Engineering across aerospace, biomedical, chemical, civil, computer, "
        "electrical, materials, and mechanical fields.",
        "source_url": "https://engineering.ucdavis.edu/",
    },
    _LS: {
        "focus": "The humanities, arts, social sciences, and physical and mathematical "
        "sciences — UC Davis's largest college.",
        "source_url": "https://ls.ucdavis.edu/",
    },
    _GSM: {
        "focus": "M.B.A. and specialized business master's education.",
        "source_url": "https://gsm.ucdavis.edu/",
    },
    _EDU: {
        "focus": "Teacher preparation, the Ph.D. in education, and the CANDEL Ed.D.",
        "source_url": "https://education.ucdavis.edu/",
    },
    _LAW: {
        "founded": "1965",
        "focus": "Public legal education with strengths in public-interest, environmental, "
        "and immigration law.",
        "source_url": "https://law.ucdavis.edu/",
    },
    _MED: {
        "focus": "Medical education, the biomedical sciences, and clinical care at UC Davis "
        "Health.",
        "source_url": "https://health.ucdavis.edu/medschool/",
    },
    _VET: {
        "founded": "1948",
        "focus": "Veterinary medicine, comparative biology, and One Health — ranked No. 1 "
        "in the U.S.",
        "source_url": "https://www.vetmed.ucdavis.edu/",
    },
    _NURS: {
        "founded": "2009",
        "focus": "Nursing education and research from master's entry to the doctorate.",
        "source_url": "https://health.ucdavis.edu/nursing/",
    },
    _GRAD: {
        "focus": "Master's and doctoral study, much of it in interdisciplinary graduate "
        "groups.",
        "source_url": "https://grad.ucdavis.edu/",
    },
}
def _about_omitted_for(name: str) -> list[str]:
    # Per-school dean/leadership names, an instructional-faculty headcount, and a verified
    # named-research-center list could not be confirmed per school this session, so they are
    # honestly omitted rather than guessed. A school's founding year is omitted only where it
    # could not be verified this session (it is provided where it was — Law, Veterinary
    # Medicine, Nursing).
    omitted = [
        "about_detail.leadership",
        "about_detail.faculty",
        "about_detail.research_centers",
    ]
    if "founded" not in (_ABOUT_DETAIL.get(name) or {}):
        omitted.append("about_detail.founded")
    return omitted


_ABOUT_OMITTED: dict[str, list[str]] = {
    name: _about_omitted_for(name) for name in _SCHOOL_WEBSITE
}

# ── Tuition constants (verified) ───────────────────────────────────────────
# Undergraduate: IPEDS 2024-25 (UNITID 110644). PUBLIC scalar = NON-RESIDENT.
_UG_OOS = 50974
_UG_INSTATE = 16774
_UG_NET = 14741
_UG_SRC = (
    "NCES College Navigator / U.S. Dept. of Education College Scorecard (UNITID 110644, "
    "2024-25)",
    "https://nces.ed.gov/collegenavigator/?id=110644",
)
# UC systemwide non-resident graduate-academic tuition + Student Services Fee (UCOP 2025-26:
# tuition $13,140 + SSF $1,290 + non-resident supplemental tuition $15,102 = $29,532; Davis
# campus-based fees are additional). Applied to academic master's degrees.
_GRAD_ACADEMIC = 29532
_GRAD_ACADEMIC_NOTE = (
    "UC systemwide non-resident graduate-academic tuition ($13,140) + Student Services Fee "
    "($1,290) + non-resident supplemental tuition ($15,102) = $29,532 (UCOP 2025-26); "
    "Davis campus-based fees are additional. California residents pay $14,430 plus fees."
)
_UCOP_SRC = (
    "UC Office of the President — 2025-26 Tuition & Fee Levels",
    "https://www.ucop.edu/operating-budget/_files/fees/202526/2025-26.pdf",
)
# Professional non-resident tuition + fees, each school's published 2025-26 figure.
_JD = 72115
_JD_SRC = (
    "UC Davis School of Law — Cost of Attendance (2025-26, non-resident tuition & fees)",
    "https://law.ucdavis.edu/admissions/financial-aid/prospective/cost-of-attendance",
)
_LLM = 65879
_LLM_SRC = (
    "UC Davis School of Law — LL.M. Cost of Tuition (2025-26)",
    "https://law.ucdavis.edu/international/llm/cost-of-tuition",
)
_MD = 60525
_MD_SRC = (
    "UC Davis School of Medicine — Cost of Attendance (2025-26, non-resident tuition & fees)",
    "https://health.ucdavis.edu/financialaid/coa-med.html",
)
_DVM = 42695
_DVM_SRC = (
    "UC Davis School of Veterinary Medicine — DVM Cost of Attendance (2025-26, non-resident "
    "tuition & fees)",
    "https://financialaid.ucdavis.edu/graduate/vet/cost/DVM2526",
)

# Professional degrees whose exact all-in non-resident total could not be verified this
# session record the verified UCOP Professional Degree Supplemental Tuition (PDST) instead of
# a guessed total.
# Professional master's whose all-in tuition & fees ARE published on the program's own cost
# page (verified 2026-06-30, same first-party basis as the J.D./M.D./D.V.M. professional rates
# above). ``program.tuition`` carries the NON-RESIDENT figure (the matcher's budget scalar for
# the out-of-state + international pool, REPAIR_BACKLOG #2); ``cost_data.breakdown`` preserves
# BOTH the California-resident and non-resident rates. The non-resident rate is the published
# resident tuition & fees plus the $12,245 professional-program nonresident supplemental tuition.
_MBA_INSTATE = 51297  # full-time M.B.A. annual tuition & fees, CA resident (entering), 2025-26
_MBA_OOS = 63542  # resident $51,297 + nonresident supplemental tuition $12,245
_MBA_SRC = (
    "UC Davis Graduate School of Management — Full-Time M.B.A. Tuition & Financial Aid (2025-26)",
    "https://gsm.ucdavis.edu/full-time-mba/tuition-financial-aid",
)
_MBA_NOTE = (
    "Full-time M.B.A. annual tuition & fees: California residents $51,297; non-residents "
    "$63,542 (the resident total plus the $12,245 nonresident supplemental tuition). Both "
    "rates ship in the breakdown; the cost card shows the resident basis while the matcher's "
    "budget signal (program.tuition) uses the non-resident rate for the out-of-state + "
    "international pool."
)
_MPH_INSTATE = 29960  # M.P.H. annual tuition & fees, CA resident, 2026-27
_MPH_OOS = 42205  # resident $29,960 + nonresident supplemental tuition $12,245
_MPH_SRC = (
    "UC Davis Health — M.P.H. Cost of Attendance (2026-27, tuition & fees)",
    "https://health.ucdavis.edu/financialaid/coa-mph.html",
)
_MPH_NOTE = (
    "M.P.H. annual tuition & fees: California residents $29,960; non-residents $42,205 (the "
    "resident total plus the $12,245 nonresident supplemental tuition). Both rates ship in "
    "the breakdown; the cost card shows the resident basis while the matcher's budget signal "
    "(program.tuition) uses the non-resident rate for the out-of-state + international pool."
)
_OMIT_MPVM = (
    "A verified all-in annual tuition figure is omitted rather than estimated: UC Davis's "
    "2025-26 M.P.V.M. Professional Degree Supplemental Tuition is $6,243 (UCOP), charged on "
    "top of base graduate tuition and fees; see the School of Veterinary Medicine's cost "
    "page."
)
_OMIT_EDD = (
    "A verified all-in annual tuition figure is omitted rather than estimated: UC Davis's "
    "2025-26 Ed.D. (CANDEL) Professional Degree Supplemental Tuition is $5,262 (UCOP), "
    "charged on top of base graduate tuition and fees."
)
_OMIT_NURSING = (
    "A verified annual tuition figure is omitted rather than estimated: the Betty Irene "
    "Moore School of Nursing programs are not listed under the UCOP Professional Degree "
    "Supplemental Tuition table for Davis; see the school's cost-of-attendance page for the "
    "current rate."
)
_FUNDED_PHD_NOTE = (
    "Admitted research-doctorate students at UC Davis are typically supported by "
    "fellowships, teaching or graduate-student-researcher appointments, and tuition/fee "
    "remission, so the published sticker is not the price funded students pay."
)

_C = _CAES
_B = _CBS
_E = _COE
_L = _LS

_CATALOG: list[dict] = [
    # ═════════ College of Agricultural and Environmental Sciences (undergraduate) ═════════
    dict(
        slug="ucdavis-animal-science-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Animal Science",
        department="Department of Animal Science", cip="01.0901", duration_months=48,
        keywords=["Animal Science", "livestock", "pre-vet"],
        description=(
            "Animal science studies the biology, nutrition, genetics, reproduction, and "
            "management of domestic and production animals, with hands-on work at UC Davis's "
            "teaching herds, flocks, and animal facilities."
        ),
        who_its_for=(
            "Students headed for veterinary school, animal agriculture, or animal biology "
            "research who want laboratory and live-animal experience alongside the science."
        ),
    ),
    dict(
        slug="ucdavis-animal-science-management-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Animal Science and Management",
        department="Department of Animal Science", cip="01.0901", duration_months=48,
        keywords=["Animal Science and Management", "agribusiness", "livestock"],
        description=(
            "This major pairs animal biology and husbandry with the economics, business, and "
            "policy of livestock and animal enterprises, preparing graduates to run and "
            "advise animal operations."
        ),
        who_its_for=(
            "Students who want the science of animal production plus the management and "
            "business skills to lead ranches, agribusinesses, or animal industries."
        ),
    ),
    dict(
        slug="ucdavis-animal-biology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Animal Biology",
        department="Department of Animal Science", cip="26.0707", duration_months=48,
        keywords=["Animal Biology", "physiology", "zoology"],
        description=(
            "Animal biology examines the physiology, behavior, genetics, and ecology of "
            "animals from cells to whole organisms across the animal kingdom, with a strong "
            "laboratory and research emphasis."
        ),
        who_its_for=(
            "Students fascinated by how animals work who are aiming at veterinary or "
            "graduate study, research, or conservation careers."
        ),
    ),
    dict(
        slug="ucdavis-agricultural-environmental-education-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in Agricultural and Environmental Education",
        department="Department of Animal Science", cip="13.1301", duration_months=48,
        keywords=["Agricultural Education", "teaching", "communication"],
        description=(
            "This major prepares students to teach and communicate agricultural, food, and "
            "environmental science in schools, extension, and community settings, combining "
            "science coursework with education and outreach."
        ),
        who_its_for=(
            "Future agriculture teachers, 4-H and extension educators, and science "
            "communicators who want both subject depth and teaching skills."
        ),
    ),
    dict(
        slug="ucdavis-atmospheric-science-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Atmospheric Science",
        department="Department of Land, Air and Water Resources", cip="40.0401",
        duration_months=48, keywords=["Atmospheric Science", "meteorology", "climate"],
        description=(
            "Atmospheric science studies the physics and dynamics of the atmosphere, "
            "weather, and climate, using mathematics, fluid dynamics, and computer modeling "
            "to understand and forecast the air around us."
        ),
        who_its_for=(
            "Students drawn to weather, climate, and air quality who enjoy physics and "
            "quantitative modeling and are aiming at meteorology or climate science."
        ),
    ),
    dict(
        slug="ucdavis-biotechnology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Biotechnology",
        department="Department of Plant Sciences", cip="26.1201", duration_months=48,
        keywords=["Biotechnology", "genetic engineering", "bioprocessing"],
        description=(
            "Biotechnology uses living systems and molecular tools — recombinant DNA, "
            "fermentation, and bioprocessing — to engineer products for agriculture, "
            "medicine, and industry, with an emphasis options spanning plant, animal, and "
            "microbial systems."
        ),
        who_its_for=(
            "Students who want to turn molecular biology into applied products and "
            "processes, headed for biotech industry or graduate research."
        ),
    ),
    dict(
        slug="ucdavis-clinical-nutrition-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Clinical Nutrition",
        department="Department of Nutrition", cip="51.3102", duration_months=48,
        keywords=["Clinical Nutrition", "dietetics", "health"],
        description=(
            "Clinical nutrition applies the science of human nutrition to disease, diet "
            "therapy, and dietetics practice, and is an accredited pathway toward becoming a "
            "registered dietitian."
        ),
        who_its_for=(
            "Students aiming to become registered dietitians or to enter clinical and "
            "public-health nutrition who want a science-heavy, professionally accredited "
            "track."
        ),
    ),
    dict(
        slug="ucdavis-community-regional-development-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Community and Regional Development",
        department="Department of Human Ecology", cip="03.0201", duration_months=48,
        keywords=["Community and Regional Development", "planning", "policy"],
        description=(
            "This major studies how communities and regions develop economically, socially, "
            "and spatially, and the policies and planning that shape housing, equity, and "
            "rural and urban change."
        ),
        who_its_for=(
            "Students drawn to community organizing, planning, nonprofit work, or local "
            "policy who want social-science grounding in how places change."
        ),
    ),
    dict(
        slug="ucdavis-entomology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Entomology",
        department="Department of Entomology and Nematology", cip="26.0702",
        duration_months=48, keywords=["Entomology", "insects", "pest management"],
        description=(
            "Entomology studies the biology, ecology, diversity, and management of insects "
            "and related arthropods — the most numerous animals on Earth — from pollinators "
            "to agricultural pests and disease vectors."
        ),
        who_its_for=(
            "Students captivated by insects who want careers in pest management, ecology, "
            "public health, or insect science research."
        ),
    ),
    dict(
        slug="ucdavis-environmental-policy-analysis-planning-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Policy Analysis and Planning",
        department="Department of Environmental Science and Policy", cip="03.0103",
        duration_months=48, keywords=["Environmental Policy", "planning", "sustainability"],
        description=(
            "This major analyzes and designs the policy and planning responses to "
            "environmental problems, combining ecology and economics with law, governance, "
            "and land-use planning."
        ),
        who_its_for=(
            "Students who want to shape environmental policy and land-use decisions and who "
            "like blending science with politics and economics."
        ),
    ),
    dict(
        slug="ucdavis-environmental-science-management-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Science and Management",
        department="Department of Environmental Science and Policy", cip="03.0104",
        duration_months=48, keywords=["Environmental Science", "ecosystems", "management"],
        description=(
            "This interdisciplinary major integrates the natural and social sciences to "
            "manage ecosystems and natural resources, addressing water, soils, biodiversity, "
            "pollution, and climate."
        ),
        who_its_for=(
            "Students who want a broad, science-grounded path into environmental "
            "consulting, resource agencies, or sustainability work."
        ),
    ),
    dict(
        slug="ucdavis-environmental-toxicology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Toxicology",
        department="Department of Environmental Toxicology", cip="03.0104",
        duration_months=48, keywords=["Environmental Toxicology", "chemistry", "health"],
        description=(
            "Environmental toxicology studies how chemicals and pollutants move through and "
            "affect organisms and ecosystems, linking chemistry, biology, and risk "
            "assessment to protect human and environmental health."
        ),
        who_its_for=(
            "Students who want to understand chemical risk and are aiming at toxicology, "
            "environmental health, or regulatory science careers."
        ),
    ),
    dict(
        slug="ucdavis-food-science-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Food Science",
        department="Department of Food Science and Technology", cip="01.1001",
        duration_months=48, keywords=["Food Science", "food safety", "processing"],
        description=(
            "Food science applies chemistry, microbiology, and engineering to how food is "
            "produced, processed, preserved, and kept safe, at one of the country's leading "
            "food-science programs."
        ),
        who_its_for=(
            "Students aiming at the food and beverage industry, food safety, or product "
            "development who want a science-and-engineering foundation."
        ),
    ),
    dict(
        slug="ucdavis-human-development-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Human Development",
        department="Department of Human Ecology", cip="19.0701", duration_months=48,
        keywords=["Human Development", "lifespan", "psychology"],
        description=(
            "Human development studies physical, cognitive, and social development across "
            "the lifespan, drawing on psychology, biology, and family and social science."
        ),
        who_its_for=(
            "Students interested in children, families, aging, or human services and "
            "preparing for careers in education, counseling, or health."
        ),
    ),
    dict(
        slug="ucdavis-hydrology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Hydrology",
        department="Department of Land, Air and Water Resources", cip="03.0205",
        duration_months=48, keywords=["Hydrology", "water resources", "watersheds"],
        description=(
            "Hydrology studies the distribution, movement, and quality of water across "
            "watersheds, rivers, and aquifers — a central concern in California — combining "
            "physics, chemistry, and earth science."
        ),
        who_its_for=(
            "Students who want to work on water supply, flooding, drought, and water quality "
            "as scientists, engineers, or resource managers."
        ),
    ),
    dict(
        slug="ucdavis-international-agricultural-development-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in International Agricultural Development",
        department="Department of Plant Sciences", cip="01.0101", duration_months=48,
        keywords=["International Agricultural Development", "global", "food systems"],
        description=(
            "This major studies agriculture, food systems, and rural development in a global "
            "and developing-world context, combining the agricultural and social sciences "
            "with international fieldwork."
        ),
        who_its_for=(
            "Students drawn to global development, food security, and international "
            "agriculture and aiming at NGOs, government, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-landscape-architecture-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Landscape Architecture",
        department="Department of Human Ecology", cip="04.0601", duration_months=48,
        keywords=["Landscape Architecture", "design", "ecology"],
        description=(
            "Landscape architecture designs outdoor spaces, sites, and landscapes, "
            "integrating ecology, hydrology, and culture with built form through design "
            "studios and an accredited professional curriculum."
        ),
        who_its_for=(
            "Students who want a creative, accredited design path into landscape "
            "architecture, planning, or ecological design."
        ),
    ),
    dict(
        slug="ucdavis-managerial-economics-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Managerial Economics",
        department="Department of Agricultural and Resource Economics", cip="01.0103",
        duration_months=48, keywords=["Managerial Economics", "business", "markets"],
        description=(
            "Managerial economics applies economic analysis to business, markets, and "
            "managerial decision-making, covering finance, marketing, accounting, and "
            "agribusiness as an applied alternative to a general economics degree."
        ),
        who_its_for=(
            "Students who want a quantitative, business-oriented economics degree headed for "
            "finance, consulting, agribusiness, or management."
        ),
    ),
    dict(
        slug="ucdavis-nutrition-science-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Nutrition Science",
        department="Department of Nutrition", cip="30.1901", duration_months=48,
        keywords=["Nutrition Science", "metabolism", "biochemistry"],
        description=(
            "Nutrition science studies the molecular and physiological roles of nutrients "
            "and metabolism in humans and animals, grounded in biochemistry and physiology."
        ),
        who_its_for=(
            "Students aiming at medical or graduate school or nutrition research who want a "
            "rigorous biochemical foundation in human nutrition."
        ),
    ),
    dict(
        slug="ucdavis-plant-sciences-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Plant Sciences",
        department="Department of Plant Sciences", cip="01.1101", duration_months=48,
        keywords=["Plant Sciences", "crops", "horticulture"],
        description=(
            "Plant sciences studies the biology, genetics, and cultivation of crop and "
            "horticultural plants — from molecular breeding to sustainable production "
            "systems — at a leading agricultural university."
        ),
        who_its_for=(
            "Students interested in crops, plant breeding, horticulture, or agroecology "
            "aiming at agriculture, biotech, or graduate research."
        ),
    ),
    dict(
        slug="ucdavis-sustainable-agriculture-food-systems-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in Sustainable Agriculture and Food Systems",
        department="Department of Land, Air and Water Resources", cip="01.0101",
        duration_months=48, keywords=["Sustainable Agriculture", "food systems", "ecology"],
        description=(
            "This major studies how to design agricultural and food systems that are "
            "ecologically sound, economically viable, and socially just, integrating "
            "agronomy, ecology, and policy."
        ),
        who_its_for=(
            "Students committed to sustainability and food justice who want to work across "
            "farming, food systems, and policy."
        ),
    ),
    dict(
        slug="ucdavis-sustainable-environmental-design-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in Sustainable Environmental Design",
        department="Department of Human Ecology", cip="04.0601", duration_months=48,
        keywords=["Sustainable Environmental Design", "design", "sustainability"],
        description=(
            "This major designs built and natural environments for ecological "
            "sustainability and human use, blending design, planning, and environmental "
            "science."
        ),
        who_its_for=(
            "Students who want to design sustainable places and systems and are drawn to "
            "design, planning, or environmental careers."
        ),
    ),
    dict(
        slug="ucdavis-viticulture-enology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Viticulture and Enology",
        department="Department of Viticulture and Enology", cip="01.0308",
        duration_months=48, keywords=["Viticulture and Enology", "wine", "grapes"],
        description=(
            "Viticulture and enology is the science of growing wine grapes and making wine, "
            "covering plant biology, soils, chemistry, and microbiology at the world's "
            "leading academic wine program."
        ),
        who_its_for=(
            "Students drawn to the science and craft of wine who are aiming at the wine "
            "industry, viticulture, or fermentation science."
        ),
    ),
    dict(
        slug="ucdavis-wildlife-fish-conservation-biology-bs", school=_C,
        degree_type="bachelors",
        program_name="Bachelor of Science in Wildlife, Fish, and Conservation Biology",
        department="Department of Wildlife, Fish and Conservation Biology", cip="03.0601",
        duration_months=48, keywords=["Wildlife", "conservation", "ecology"],
        description=(
            "This major studies the ecology, management, and conservation of wildlife, fish, "
            "and their habitats, combining field biology, population ecology, and "
            "conservation policy."
        ),
        who_its_for=(
            "Students who want to work in wildlife conservation, fisheries, or ecology as "
            "biologists, managers, or researchers."
        ),
    ),
    dict(
        slug="ucdavis-global-disease-biology-bs", school=_C, degree_type="bachelors",
        program_name="Bachelor of Science in Global Disease Biology",
        department="Department of Plant Pathology", cip="26.0102", duration_months=48,
        keywords=["Global Disease Biology", "epidemiology", "One Health"],
        description=(
            "Global disease biology studies how diseases of plants, animals, and humans "
            "emerge, spread, and are controlled across interconnected systems, a One Health "
            "approach spanning biology and public health."
        ),
        who_its_for=(
            "Pre-health and pre-vet students and future epidemiologists who want an "
            "integrative, systems view of disease."
        ),
    ),
    # ═════════ College of Biological Sciences (undergraduate) ═════════
    dict(
        slug="ucdavis-biological-sciences-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Biological Sciences",
        department="College of Biological Sciences", cip="26.0101", duration_months=48,
        keywords=["Biological Sciences", "biology", "pre-health"],
        description=(
            "This broad major builds a foundation across molecular, cellular, organismal, "
            "and ecological biology, letting students range widely before specializing — a "
            "common pre-health and pre-graduate path."
        ),
        who_its_for=(
            "Students who want a flexible, comprehensive biology degree, including many "
            "preparing for medical, dental, or graduate school."
        ),
    ),
    dict(
        slug="ucdavis-biochemistry-molecular-biology-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Biochemistry and Molecular Biology",
        department="Department of Molecular and Cellular Biology", cip="26.0202",
        duration_months=48, keywords=["Biochemistry", "molecular biology", "pre-med"],
        description=(
            "This major studies the chemistry of life — how molecules, enzymes, and "
            "metabolic pathways drive cellular function — with heavy laboratory and research "
            "training."
        ),
        who_its_for=(
            "Students aiming at biomedical research, medical school, or biotech who want "
            "molecular depth and bench experience."
        ),
    ),
    dict(
        slug="ucdavis-cell-biology-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Cell Biology",
        department="Department of Molecular and Cellular Biology", cip="26.0407",
        duration_months=48, keywords=["Cell Biology", "molecular", "research"],
        description=(
            "Cell biology studies the structure, function, and behavior of cells and their "
            "organelles, from membrane dynamics to cell signaling and division."
        ),
        who_its_for=(
            "Students drawn to how cells work who are aiming at research, medicine, or "
            "biotechnology."
        ),
    ),
    dict(
        slug="ucdavis-genetics-genomics-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Genetics and Genomics",
        department="Department of Molecular and Cellular Biology", cip="26.0801",
        duration_months=48, keywords=["Genetics", "genomics", "bioinformatics"],
        description=(
            "This major studies heredity, gene function, and the structure and analysis of "
            "whole genomes, blending classical genetics with modern genomics and "
            "computational analysis."
        ),
        who_its_for=(
            "Students interested in DNA, genomics, and bioinformatics aiming at research, "
            "medicine, or the genomics industry."
        ),
    ),
    dict(
        slug="ucdavis-evolution-ecology-biodiversity-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Evolution, Ecology and Biodiversity",
        department="Department of Evolution and Ecology", cip="26.1301", duration_months=48,
        keywords=["Evolution", "Ecology", "Biodiversity"],
        description=(
            "This major studies evolutionary processes, ecological interactions, and the "
            "diversity of life, from population genetics to ecosystems and conservation."
        ),
        who_its_for=(
            "Students fascinated by evolution and the natural world, aiming at ecology, "
            "conservation, or evolutionary biology research."
        ),
    ),
    dict(
        slug="ucdavis-molecular-medical-microbiology-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Molecular and Medical Microbiology",
        department="Department of Microbiology and Molecular Genetics", cip="26.0503",
        duration_months=48, keywords=["Microbiology", "infectious disease", "immunology"],
        description=(
            "This major studies microorganisms — bacteria, viruses, and fungi — and their "
            "roles in disease, immunity, and medicine, with molecular and laboratory "
            "emphasis."
        ),
        who_its_for=(
            "Pre-health students and future microbiologists interested in infectious "
            "disease, immunology, and medical microbiology."
        ),
    ),
    dict(
        slug="ucdavis-human-biology-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Human Biology",
        department="Department of Neurobiology, Physiology and Behavior", cip="26.0101",
        duration_months=48, keywords=["Human Biology", "physiology", "pre-med"],
        description=(
            "Human biology integrates human anatomy, physiology, genetics, and health into "
            "one major, a popular interdisciplinary path for students headed to the health "
            "professions."
        ),
        who_its_for=(
            "Pre-medical and pre-health students who want a human-focused, integrative "
            "biology degree."
        ),
    ),
    dict(
        slug="ucdavis-neurobiology-physiology-behavior-bs", school=_B,
        degree_type="bachelors",
        program_name="Bachelor of Science in Neurobiology, Physiology and Behavior",
        department="Department of Neurobiology, Physiology and Behavior", cip="26.1502",
        duration_months=48, keywords=["Neurobiology", "physiology", "behavior"],
        description=(
            "This major studies how nervous systems, organ physiology, and behavior work in "
            "animals and humans, spanning neuroscience, physiology, and behavioral biology."
        ),
        who_its_for=(
            "Students drawn to the brain, body, and behavior, including many preparing for "
            "medicine or neuroscience research."
        ),
    ),
    dict(
        slug="ucdavis-plant-biology-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Plant Biology",
        department="Department of Plant Biology", cip="26.0301", duration_months=48,
        keywords=["Plant Biology", "botany", "physiology"],
        description=(
            "Plant biology studies the biology, physiology, genetics, and development of "
            "plants from cells to ecosystems, including their roles in food, energy, and "
            "the environment."
        ),
        who_its_for=(
            "Students interested in how plants work, aiming at plant science, biotech, or "
            "ecology research."
        ),
    ),
    dict(
        slug="ucdavis-systems-synthetic-biology-bs", school=_B, degree_type="bachelors",
        program_name="Bachelor of Science in Systems and Synthetic Biology",
        department="Department of Plant Biology", cip="26.1102", duration_months=48,
        keywords=["Systems Biology", "Synthetic Biology", "bioengineering"],
        description=(
            "This major models biological systems quantitatively and engineers new "
            "biological functions, combining molecular biology with mathematics, computing, "
            "and design."
        ),
        who_its_for=(
            "Students who like both biology and quantitative engineering and want to design "
            "and model living systems."
        ),
    ),
    # ═════════ College of Engineering (undergraduate) ═════════
    dict(
        slug="ucdavis-aerospace-science-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Aerospace Science and Engineering",
        department="Department of Mechanical and Aerospace Engineering", cip="14.0201",
        duration_months=48, keywords=["Aerospace Engineering", "aircraft", "spacecraft"],
        description=(
            "Aerospace science and engineering covers the aerodynamics, propulsion, "
            "structures, and control of aircraft, spacecraft, and flight systems, grounded "
            "in mechanics and design."
        ),
        who_its_for=(
            "Students drawn to flight and space systems who want a mechanics- and "
            "design-heavy engineering degree."
        ),
    ),
    dict(
        slug="ucdavis-biochemical-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Biochemical Engineering",
        department="Department of Chemical Engineering", cip="14.2701", duration_months=48,
        keywords=["Biochemical Engineering", "bioprocessing", "fermentation"],
        description=(
            "Biochemical engineering applies chemical engineering to biological processes — "
            "fermentation, enzymes, and bioproduct manufacturing — bridging biology and "
            "process design."
        ),
        who_its_for=(
            "Students who want to engineer biological processes for biotech, "
            "pharmaceuticals, or sustainable manufacturing."
        ),
    ),
    dict(
        slug="ucdavis-biological-systems-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Biological Systems Engineering",
        department="Department of Biological and Agricultural Engineering", cip="14.0301",
        duration_months=48, keywords=["Biological Systems Engineering", "agriculture", "water"],
        description=(
            "Biological systems engineering applies engineering to biological, agricultural, "
            "food, and environmental systems, from irrigation and food processing to "
            "bioenergy and ecological engineering."
        ),
        who_its_for=(
            "Students who want to engineer solutions for food, water, agriculture, and the "
            "environment."
        ),
    ),
    dict(
        slug="ucdavis-biomedical-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.0501", duration_months=48,
        keywords=["Biomedical Engineering", "medical devices", "imaging"],
        description=(
            "Biomedical engineering applies engineering principles to medicine and biology — "
            "designing devices, imaging, biomaterials, and tissue engineering — alongside "
            "UC Davis's medical and veterinary schools."
        ),
        who_its_for=(
            "Students who want to build medical technology and bridge engineering with "
            "biology and medicine."
        ),
    ),
    dict(
        slug="ucdavis-chemical-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Chemical Engineering",
        department="Department of Chemical Engineering", cip="14.0701", duration_months=48,
        keywords=["Chemical Engineering", "process", "materials"],
        description=(
            "Chemical engineering designs the processes that transform raw materials into "
            "chemicals, fuels, materials, and energy, built on thermodynamics, transport, "
            "and reaction engineering."
        ),
        who_its_for=(
            "Students strong in chemistry and math who want to design industrial processes "
            "and products."
        ),
    ),
    dict(
        slug="ucdavis-civil-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Civil Engineering",
        department="Department of Civil and Environmental Engineering", cip="14.0801",
        duration_months=48, keywords=["Civil Engineering", "infrastructure", "structures"],
        description=(
            "Civil engineering designs and builds the infrastructure that society depends "
            "on — structures, transportation, water, and geotechnical systems — with "
            "emphasis on safety and sustainability."
        ),
        who_its_for=(
            "Students who want to design bridges, buildings, transportation, and water "
            "infrastructure."
        ),
    ),
    dict(
        slug="ucdavis-computer-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Engineering",
        department="Department of Electrical and Computer Engineering", cip="14.0901",
        duration_months=48, keywords=["Computer Engineering", "hardware", "embedded systems"],
        description=(
            "Computer engineering works at the hardware-software interface, designing "
            "processors, embedded systems, and digital circuits along with the software that "
            "runs on them."
        ),
        who_its_for=(
            "Students who like both hardware and software and want to design computing "
            "systems end to end."
        ),
    ),
    dict(
        slug="ucdavis-computer-science-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Computer Science",
        department="Department of Computer Science", cip="11.0701", duration_months=48,
        keywords=["Computer Science", "algorithms", "software"],
        description=(
            "Computer science studies algorithms, software, computation, and the theory and "
            "practice of computing, from data structures and systems to artificial "
            "intelligence."
        ),
        who_its_for=(
            "Students who want to build software and understand computation, headed for "
            "tech, research, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-electrical-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Electrical Engineering",
        department="Department of Electrical and Computer Engineering", cip="14.1001",
        duration_months=48, keywords=["Electrical Engineering", "circuits", "signals"],
        description=(
            "Electrical engineering covers the theory and design of electrical and "
            "electronic systems — circuits, signals, communications, and power — from "
            "microchips to energy grids."
        ),
        who_its_for=(
            "Students drawn to electronics, signals, and power systems who want a broad, "
            "math-rich engineering degree."
        ),
    ),
    dict(
        slug="ucdavis-environmental-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Environmental Engineering",
        department="Department of Civil and Environmental Engineering", cip="14.1401",
        duration_months=48, keywords=["Environmental Engineering", "water", "pollution"],
        description=(
            "Environmental engineering designs solutions for water and air quality, "
            "pollution control, and environmental protection, combining engineering with "
            "chemistry and ecology."
        ),
        who_its_for=(
            "Students who want to engineer clean water, clean air, and a healthier "
            "environment."
        ),
    ),
    dict(
        slug="ucdavis-materials-science-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Materials Science and Engineering",
        department="Department of Materials Science and Engineering", cip="14.1801",
        duration_months=48, keywords=["Materials Science", "metals", "polymers"],
        description=(
            "Materials science and engineering studies the structure, properties, and "
            "processing of metals, ceramics, polymers, and electronic and composite "
            "materials, and how to design new ones."
        ),
        who_its_for=(
            "Students who want to understand and engineer the materials behind every "
            "technology, from chips to aerospace."
        ),
    ),
    dict(
        slug="ucdavis-mechanical-engineering-bs", school=_E, degree_type="bachelors",
        program_name="Bachelor of Science in Mechanical Engineering",
        department="Department of Mechanical and Aerospace Engineering", cip="14.1901",
        duration_months=48, keywords=["Mechanical Engineering", "machines", "thermodynamics"],
        description=(
            "Mechanical engineering covers the design, mechanics, dynamics, and "
            "thermodynamics of machines and mechanical systems, from robotics and energy to "
            "manufacturing."
        ),
        who_its_for=(
            "Students who want a versatile engineering degree spanning machines, energy, "
            "robotics, and design."
        ),
    ),
    # ═════════ College of Letters and Science — Humanities & Arts (undergraduate) ═════════
    dict(
        slug="ucdavis-african-american-african-studies-ba", school=_L,
        degree_type="bachelors",
        program_name="Bachelor of Arts in African American and African Studies",
        department="Department of African American and African Studies", cip="05.0201",
        duration_months=48, keywords=["African American Studies", "Africa", "diaspora"],
        description=(
            "This major studies the history, culture, politics, and societies of African and "
            "African-diaspora peoples through an interdisciplinary humanities and "
            "social-science lens."
        ),
        who_its_for=(
            "Students drawn to the histories and cultures of the African diaspora who want "
            "interdisciplinary grounding for law, public service, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-american-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in American Studies",
        department="American Studies Program", cip="05.0102", duration_months=48,
        keywords=["American Studies", "culture", "interdisciplinary"],
        description=(
            "American studies is the interdisciplinary study of U.S. culture, history, and "
            "society, combining literature, history, media, and the social sciences."
        ),
        who_its_for=(
            "Students who want a flexible, interdisciplinary lens on American culture and "
            "society."
        ),
    ),
    dict(
        slug="ucdavis-art-history-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Art History",
        department="Department of Art and Art History", cip="50.0703", duration_months=48,
        keywords=["Art History", "visual art", "criticism"],
        description=(
            "Art history studies the history, theory, and interpretation of visual art and "
            "architecture across cultures and periods."
        ),
        who_its_for=(
            "Students drawn to art, museums, and visual culture, aiming at curatorial, "
            "academic, or arts careers."
        ),
    ),
    dict(
        slug="ucdavis-art-studio-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Art Studio",
        department="Department of Art and Art History", cip="50.0702", duration_months=48,
        keywords=["Art Studio", "studio art", "practice"],
        description=(
            "Art studio is the practice of making visual art across media — painting, "
            "sculpture, photography, and new media — grounded in critique and art history."
        ),
        who_its_for=(
            "Students who want to develop as practicing artists with conceptual and "
            "technical depth."
        ),
    ),
    dict(
        slug="ucdavis-asian-american-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Asian American Studies",
        department="Department of Asian American Studies", cip="05.0200", duration_months=48,
        keywords=["Asian American Studies", "ethnic studies", "history"],
        description=(
            "This major studies the histories, communities, and experiences of Asian "
            "Americans through history, literature, and the social sciences."
        ),
        who_its_for=(
            "Students interested in Asian American communities and ethnic studies for "
            "careers in law, education, advocacy, or research."
        ),
    ),
    dict(
        slug="ucdavis-chicana-chicano-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Chicana/Chicano Studies",
        department="Department of Chicana and Chicano Studies", cip="05.0202",
        duration_months=48, keywords=["Chicana/Chicano Studies", "Latino", "ethnic studies"],
        description=(
            "This major studies the history, culture, politics, and art of Chicana/o and "
            "Latina/o peoples in the United States through an interdisciplinary lens."
        ),
        who_its_for=(
            "Students engaged with Latino communities and social justice, headed for law, "
            "education, public service, or research."
        ),
    ),
    dict(
        slug="ucdavis-chinese-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Chinese",
        department="Department of East Asian Languages and Cultures", cip="16.0301",
        duration_months=48, keywords=["Chinese", "language", "East Asia"],
        description=(
            "This major develops advanced Chinese language proficiency alongside the study "
            "of Chinese literature, culture, and history."
        ),
        who_its_for=(
            "Students who want fluency in Chinese and cultural depth for careers spanning "
            "business, diplomacy, and academia."
        ),
    ),
    dict(
        slug="ucdavis-japanese-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Japanese",
        department="Department of East Asian Languages and Cultures", cip="16.0302",
        duration_months=48, keywords=["Japanese", "language", "East Asia"],
        description=(
            "This major develops advanced Japanese language proficiency together with the "
            "study of Japanese literature, culture, and history."
        ),
        who_its_for=(
            "Students who want Japanese fluency and cultural fluency for international "
            "careers or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-east-asian-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in East Asian Studies",
        department="East Asian Studies Program", cip="05.0104", duration_months=48,
        keywords=["East Asian Studies", "China", "Japan"],
        description=(
            "East Asian studies is the interdisciplinary study of the societies, histories, "
            "and cultures of East Asia, integrating language with history and the social "
            "sciences."
        ),
        who_its_for=(
            "Students drawn to East Asia who want a broad, interdisciplinary regional "
            "education."
        ),
    ),
    dict(
        slug="ucdavis-cinema-digital-media-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Cinema and Digital Media",
        department="Department of Cinema and Digital Media", cip="50.0601", duration_months=48,
        keywords=["Cinema", "Digital Media", "film"],
        description=(
            "This major studies film, screen media, and digital media as art and cultural "
            "form, combining critical analysis with production and digital media practice."
        ),
        who_its_for=(
            "Students fascinated by film and digital media who want both critical and "
            "creative training."
        ),
    ),
    dict(
        slug="ucdavis-classical-civilization-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Classical Civilization",
        department="Classics Program", cip="16.1200", duration_months=48,
        keywords=["Classics", "Greece", "Rome"],
        description=(
            "Classical civilization studies the languages, literature, history, and culture "
            "of ancient Greece and Rome and their enduring influence."
        ),
        who_its_for=(
            "Students drawn to the ancient world and its languages, building a foundation "
            "for law, the humanities, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-comparative-literature-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Comparative Literature",
        department="Department of Comparative Literature", cip="16.0104", duration_months=48,
        keywords=["Comparative Literature", "translation", "world literature"],
        description=(
            "Comparative literature studies literature across languages, cultures, and "
            "national traditions, with attention to translation and literary theory."
        ),
        who_its_for=(
            "Students who love literature across cultures and want a globally minded "
            "humanities degree."
        ),
    ),
    dict(
        slug="ucdavis-design-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Design",
        department="Department of Design", cip="50.0404", duration_months=48,
        keywords=["Design", "visual design", "user experience"],
        description=(
            "This major covers visual, product, spatial, and interaction design, pairing "
            "design theory and history with hands-on studio practice."
        ),
        who_its_for=(
            "Students who want to become designers across graphic, product, and "
            "user-experience fields."
        ),
    ),
    dict(
        slug="ucdavis-english-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in English",
        department="Department of English", cip="23.0101", duration_months=48,
        keywords=["English", "literature", "writing"],
        description=(
            "English studies literature, writing, and literary analysis across the "
            "Anglophone tradition, with options in creative writing and critical theory."
        ),
        who_its_for=(
            "Students who love reading and writing and want strong analytical and "
            "communication skills for many careers."
        ),
    ),
    dict(
        slug="ucdavis-french-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in French",
        department="Department of French and Italian", cip="16.0901", duration_months=48,
        keywords=["French", "language", "literature"],
        description=(
            "This major develops French language proficiency alongside the study of French "
            "and Francophone literature and culture."
        ),
        who_its_for=(
            "Students who want French fluency and cultural depth for international or "
            "academic careers."
        ),
    ),
    dict(
        slug="ucdavis-italian-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Italian",
        department="Department of French and Italian", cip="16.0902", duration_months=48,
        keywords=["Italian", "language", "literature"],
        description=(
            "This major develops Italian language proficiency together with the study of "
            "Italian literature, art, and culture."
        ),
        who_its_for=(
            "Students drawn to Italian language and culture for the humanities, arts, or "
            "international work."
        ),
    ),
    dict(
        slug="ucdavis-german-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in German",
        department="Department of German and Russian", cip="16.0501", duration_months=48,
        keywords=["German", "language", "literature"],
        description=(
            "This major develops German language proficiency alongside the study of German "
            "literature, philosophy, and culture."
        ),
        who_its_for=(
            "Students who want German fluency for the humanities, science, or international "
            "careers."
        ),
    ),
    dict(
        slug="ucdavis-russian-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Russian",
        department="Department of German and Russian", cip="16.0402", duration_months=48,
        keywords=["Russian", "language", "literature"],
        description=(
            "This major develops Russian language proficiency together with the study of "
            "Russian literature, history, and culture."
        ),
        who_its_for=(
            "Students drawn to Russian language and culture for academic, diplomatic, or "
            "research careers."
        ),
    ),
    dict(
        slug="ucdavis-spanish-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Spanish",
        department="Department of Spanish and Portuguese", cip="16.0905", duration_months=48,
        keywords=["Spanish", "language", "Hispanic cultures"],
        description=(
            "This major develops Spanish language proficiency alongside the study of "
            "Spanish, Latin American, and U.S. Latino literature and cultures."
        ),
        who_its_for=(
            "Students who want Spanish fluency and cultural fluency for careers in "
            "education, health, law, or international work."
        ),
    ),
    dict(
        slug="ucdavis-gender-sexuality-womens-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Gender, Sexuality and Women's Studies",
        department="Department of Gender, Sexuality and Women's Studies", cip="05.0207",
        duration_months=48, keywords=["Gender Studies", "sexuality", "feminism"],
        description=(
            "This major studies gender and sexuality as categories shaping society, culture, "
            "and power, drawing on history, the social sciences, and the humanities."
        ),
        who_its_for=(
            "Students engaged with gender and social justice, headed for law, policy, "
            "health, or advocacy."
        ),
    ),
    dict(
        slug="ucdavis-history-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in History",
        department="Department of History", cip="54.0101", duration_months=48,
        keywords=["History", "research", "analysis"],
        description=(
            "History studies the human past — events, societies, and ideas — and how "
            "historians interpret evidence across regions and eras."
        ),
        who_its_for=(
            "Students who want to research, analyze, and write, building skills for law, "
            "education, public service, and beyond."
        ),
    ),
    dict(
        slug="ucdavis-linguistics-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Linguistics",
        department="Department of Linguistics", cip="16.0102", duration_months=48,
        keywords=["Linguistics", "language", "phonetics"],
        description=(
            "Linguistics is the scientific study of language — its sounds, structure, "
            "meaning, and use — spanning phonetics, syntax, semantics, and language change."
        ),
        who_its_for=(
            "Students fascinated by how language works, with paths into tech, speech "
            "science, education, or research."
        ),
    ),
    dict(
        slug="ucdavis-medieval-early-modern-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Medieval and Early Modern Studies",
        department="Medieval and Early Modern Studies Program", cip="30.1301",
        duration_months=48, keywords=["Medieval Studies", "early modern", "history"],
        description=(
            "This interdisciplinary major studies the medieval and early-modern European "
            "world across history, literature, art, and religion."
        ),
        who_its_for=(
            "Students drawn to the pre-modern past who want an interdisciplinary humanities "
            "education."
        ),
    ),
    dict(
        slug="ucdavis-middle-east-south-asia-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Middle East/South Asia Studies",
        department="Middle East/South Asia Studies Program", cip="05.0110",
        duration_months=48, keywords=["Middle East", "South Asia", "area studies"],
        description=(
            "This major is the interdisciplinary study of the societies, histories, "
            "languages, and cultures of the Middle East and South Asia."
        ),
        who_its_for=(
            "Students interested in these regions for careers in policy, diplomacy, "
            "journalism, or academia."
        ),
    ),
    dict(
        slug="ucdavis-music-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Music",
        department="Department of Music", cip="50.0901", duration_months=48,
        keywords=["Music", "performance", "composition"],
        description=(
            "This major studies music performance, theory, composition, and history, with "
            "ensembles, technology, and scholarship."
        ),
        who_its_for=(
            "Students who want to grow as musicians and scholars across performance, "
            "composition, and music studies."
        ),
    ),
    dict(
        slug="ucdavis-native-american-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Native American Studies",
        department="Department of Native American Studies", cip="05.0202", duration_months=48,
        keywords=["Native American Studies", "Indigenous", "sovereignty"],
        description=(
            "This major studies the histories, cultures, languages, and sovereignty of "
            "Native American and Indigenous peoples through an interdisciplinary lens."
        ),
        who_its_for=(
            "Students engaged with Indigenous communities and issues, headed for law, "
            "policy, education, or research."
        ),
    ),
    dict(
        slug="ucdavis-philosophy-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Philosophy",
        department="Department of Philosophy", cip="38.0101", duration_months=48,
        keywords=["Philosophy", "logic", "ethics"],
        description=(
            "Philosophy examines fundamental questions of knowledge, reality, ethics, mind, "
            "and reasoning, training rigorous argument and analysis."
        ),
        who_its_for=(
            "Students who love big questions and rigorous reasoning, building strong "
            "foundations for law, policy, and many fields."
        ),
    ),
    dict(
        slug="ucdavis-religious-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Religious Studies",
        department="Religious Studies Program", cip="38.0201", duration_months=48,
        keywords=["Religious Studies", "religion", "culture"],
        description=(
            "Religious studies examines religious traditions, texts, and practices across "
            "cultures and history through a comparative, humanistic lens."
        ),
        who_its_for=(
            "Students curious about religion and culture, headed for law, public service, "
            "education, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-theatre-dance-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Theatre and Dance",
        department="Department of Theatre and Dance", cip="50.0501", duration_months=48,
        keywords=["Theatre", "Dance", "performance"],
        description=(
            "This major studies performance, dramatic literature, and the practice of "
            "theatre and dance, combining studio work with history and theory."
        ),
        who_its_for=(
            "Students who want to perform, create, and study theatre and dance with both "
            "practice and scholarship."
        ),
    ),
    # ═════════ College of Letters and Science — Social Sciences (undergraduate) ═════════
    dict(
        slug="ucdavis-anthropology-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Anthropology",
        department="Department of Anthropology", cip="45.0201", duration_months=48,
        keywords=["Anthropology", "culture", "archaeology"],
        description=(
            "Anthropology studies human cultures, biology, and societies across time and "
            "place, spanning cultural anthropology, archaeology, and biological "
            "anthropology."
        ),
        who_its_for=(
            "Students curious about humanity in all its forms, headed for research, "
            "heritage, global health, or public service."
        ),
    ),
    dict(
        slug="ucdavis-cognitive-science-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Cognitive Science",
        department="Cognitive Science Program", cip="30.2501", duration_months=48,
        keywords=["Cognitive Science", "mind", "AI"],
        description=(
            "Cognitive science studies the mind and intelligence across psychology, "
            "neuroscience, linguistics, philosophy, and computation."
        ),
        who_its_for=(
            "Students who want an interdisciplinary path to understanding the mind, with "
            "links to AI, UX, and neuroscience."
        ),
    ),
    dict(
        slug="ucdavis-communication-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Communication",
        department="Department of Communication", cip="09.0101", duration_months=48,
        keywords=["Communication", "media", "social science"],
        description=(
            "Communication studies how people create, share, and are affected by messages "
            "and media, using social-science methods to study interpersonal and mass "
            "communication."
        ),
        who_its_for=(
            "Students interested in media, persuasion, and human interaction, headed for "
            "media, marketing, or research."
        ),
    ),
    dict(
        slug="ucdavis-economics-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Economics",
        department="Department of Economics", cip="45.0601", duration_months=48,
        keywords=["Economics", "markets", "policy"],
        description=(
            "Economics studies how individuals, firms, and societies allocate scarce "
            "resources, combining theory, data, and policy across micro and macro "
            "economics."
        ),
        who_its_for=(
            "Students who want analytical, quantitative training for careers in business, "
            "finance, policy, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-international-relations-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in International Relations",
        department="Department of Political Science", cip="45.0901", duration_months=48,
        keywords=["International Relations", "diplomacy", "global"],
        description=(
            "International relations studies relations among states — diplomacy, conflict, "
            "trade, and global institutions — drawing on political science, economics, and "
            "history."
        ),
        who_its_for=(
            "Students drawn to global affairs and diplomacy, headed for government, NGOs, "
            "or international business."
        ),
    ),
    dict(
        slug="ucdavis-political-science-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Political Science",
        department="Department of Political Science", cip="45.1001", duration_months=48,
        keywords=["Political Science", "government", "policy"],
        description=(
            "Political science studies government, political behavior, institutions, and "
            "political theory across American, comparative, and international politics."
        ),
        who_its_for=(
            "Students interested in government and politics, with paths into law, policy, "
            "campaigns, and public service."
        ),
    ),
    dict(
        slug="ucdavis-psychology-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Psychology",
        department="Department of Psychology", cip="42.0101", duration_months=48,
        keywords=["Psychology", "behavior", "cognition"],
        description=(
            "Psychology is the science of mind and behavior, spanning cognitive, "
            "developmental, social, and biological approaches with strong research methods."
        ),
        who_its_for=(
            "Students fascinated by why people think and act as they do, headed for health, "
            "research, education, or business."
        ),
    ),
    dict(
        slug="ucdavis-science-technology-studies-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Science and Technology Studies",
        department="Science and Technology Studies Program", cip="30.1501",
        duration_months=48, keywords=["Science and Technology Studies", "society", "history"],
        description=(
            "Science and technology studies examines how science and technology shape, and "
            "are shaped by, society, history, and politics."
        ),
        who_its_for=(
            "Students who want to understand the social context of science and tech, headed "
            "for policy, law, journalism, or research."
        ),
    ),
    dict(
        slug="ucdavis-sociology-ba", school=_L, degree_type="bachelors",
        program_name="Bachelor of Arts in Sociology",
        department="Department of Sociology", cip="45.1101", duration_months=48,
        keywords=["Sociology", "society", "inequality"],
        description=(
            "Sociology studies the structure and dynamics of human societies, groups, and "
            "institutions, with attention to inequality, organizations, and social change."
        ),
        who_its_for=(
            "Students interested in society and social justice, headed for law, social "
            "work, policy, or research."
        ),
    ),
    # ═════════ College of Letters and Science — Physical & Mathematical Sciences ═════════
    dict(
        slug="ucdavis-chemistry-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Chemistry",
        department="Department of Chemistry", cip="40.0501", duration_months=48,
        keywords=["Chemistry", "molecules", "reactions"],
        description=(
            "Chemistry studies the composition, structure, and reactions of matter across "
            "organic, inorganic, physical, and analytical chemistry, with extensive "
            "laboratory work."
        ),
        who_its_for=(
            "Students who want a rigorous chemistry foundation for research, medicine, or "
            "the chemical and pharmaceutical industries."
        ),
    ),
    dict(
        slug="ucdavis-applied-chemistry-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Applied Chemistry",
        department="Department of Chemistry", cip="40.0501", duration_months=48,
        keywords=["Applied Chemistry", "industry", "materials"],
        description=(
            "Applied chemistry orients the chemistry curriculum toward industrial and "
            "applied problems, adding engineering and materials coursework for "
            "industry-bound chemists."
        ),
        who_its_for=(
            "Students who want chemistry aimed squarely at industry and applied research."
        ),
    ),
    dict(
        slug="ucdavis-chemical-physics-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Chemical Physics",
        department="Department of Chemistry", cip="40.0508", duration_months=48,
        keywords=["Chemical Physics", "quantum", "spectroscopy"],
        description=(
            "Chemical physics studies the physics underlying chemical structure and "
            "reactions, blending quantum mechanics, thermodynamics, and spectroscopy."
        ),
        who_its_for=(
            "Students who want the deepest physical foundation of chemistry, aiming at "
            "research or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-medicinal-chemistry-drug-design-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Medicinal Chemistry and Drug Design",
        department="Department of Chemistry", cip="40.0510", duration_months=48,
        keywords=["Medicinal Chemistry", "drug design", "pharmaceutical"],
        description=(
            "This major studies the chemistry of designing and developing pharmaceutical "
            "drugs, linking organic chemistry, biochemistry, and pharmacology."
        ),
        who_its_for=(
            "Students aiming at pharmaceutical research or graduate study who want to design "
            "the molecules that become medicines."
        ),
    ),
    dict(
        slug="ucdavis-geology-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Geology",
        department="Department of Earth and Planetary Sciences", cip="40.0601",
        duration_months=48, keywords=["Geology", "earth science", "field work"],
        description=(
            "Geology studies the Earth's materials, structure, and history — rocks, "
            "tectonics, and surface processes — with extensive field and laboratory work."
        ),
        who_its_for=(
            "Students who love the Earth and field science, headed for geoscience, energy, "
            "or environmental careers."
        ),
    ),
    dict(
        slug="ucdavis-marine-coastal-science-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Marine and Coastal Science",
        department="Department of Earth and Planetary Sciences", cip="40.0607",
        duration_months=48, keywords=["Marine Science", "coastal", "oceans"],
        description=(
            "This interdisciplinary major studies ocean and coastal systems, with tracks in "
            "coastal processes and chemistry, the ocean-Earth system, and marine ecology, "
            "drawing on the Bodega Marine Laboratory."
        ),
        who_its_for=(
            "Students drawn to oceans and coasts, headed for marine science, conservation, "
            "or environmental careers."
        ),
    ),
    dict(
        slug="ucdavis-physics-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Physics",
        department="Department of Physics and Astronomy", cip="40.0801", duration_months=48,
        keywords=["Physics", "mechanics", "quantum"],
        description=(
            "Physics studies matter, energy, and the fundamental laws of the universe, from "
            "mechanics and electromagnetism to quantum and condensed-matter physics."
        ),
        who_its_for=(
            "Students who want the deepest quantitative science foundation, headed for "
            "research, engineering, or graduate study."
        ),
    ),
    dict(
        slug="ucdavis-applied-physics-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Applied Physics",
        department="Department of Physics and Astronomy", cip="40.0801", duration_months=48,
        keywords=["Applied Physics", "technology", "devices"],
        description=(
            "Applied physics applies physics to technology and real-world systems, bridging "
            "fundamental physics with engineering and devices."
        ),
        who_its_for=(
            "Students who want physics aimed at technology and applied research."
        ),
    ),
    dict(
        slug="ucdavis-mathematics-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Mathematics",
        department="Department of Mathematics", cip="27.0101", duration_months=48,
        keywords=["Mathematics", "analysis", "algebra"],
        description=(
            "Mathematics is the abstract study of number, structure, space, and change, "
            "spanning analysis, algebra, geometry, and topology."
        ),
        who_its_for=(
            "Students who love rigorous reasoning and abstraction, with paths into tech, "
            "finance, education, and research."
        ),
    ),
    dict(
        slug="ucdavis-applied-mathematics-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Applied Mathematics",
        department="Department of Mathematics", cip="27.0301", duration_months=48,
        keywords=["Applied Mathematics", "modeling", "computation"],
        description=(
            "Applied mathematics uses mathematics to model and solve problems in science, "
            "engineering, and industry, emphasizing modeling and numerical methods."
        ),
        who_its_for=(
            "Students who want mathematics with direct real-world application in science "
            "and industry."
        ),
    ),
    dict(
        slug="ucdavis-mathematical-analytics-operations-research-bs", school=_L,
        degree_type="bachelors",
        program_name="Bachelor of Science in Mathematical Analytics and Operations Research",
        department="Department of Mathematics", cip="27.0305", duration_months=48,
        keywords=["Operations Research", "optimization", "analytics"],
        description=(
            "This major applies mathematical optimization, modeling, and quantitative "
            "decision analysis to business, logistics, and engineering problems."
        ),
        who_its_for=(
            "Students who want to use math for optimization and analytics in business, "
            "logistics, and data-driven decisions."
        ),
    ),
    dict(
        slug="ucdavis-mathematical-scientific-computation-bs", school=_L,
        degree_type="bachelors",
        program_name="Bachelor of Science in Mathematical and Scientific Computation",
        department="Department of Mathematics", cip="27.0303", duration_months=48,
        keywords=["Scientific Computation", "numerical methods", "computing"],
        description=(
            "This major develops computational methods for solving mathematical and "
            "scientific problems, combining mathematics with programming and numerical "
            "analysis."
        ),
        who_its_for=(
            "Students who want to bridge mathematics and computing for scientific and "
            "technical work."
        ),
    ),
    dict(
        slug="ucdavis-statistics-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Statistics",
        department="Department of Statistics", cip="27.0501", duration_months=48,
        keywords=["Statistics", "data", "inference"],
        description=(
            "Statistics is the theory and methods of collecting, analyzing, and inferring "
            "from data, from probability and inference to statistical computing."
        ),
        who_its_for=(
            "Students who want rigorous data skills for careers in data science, analytics, "
            "and research."
        ),
    ),
    dict(
        slug="ucdavis-data-science-bs", school=_L, degree_type="bachelors",
        program_name="Bachelor of Science in Data Science",
        department="Department of Statistics", cip="30.7001", duration_months=48,
        keywords=["Data Science", "machine learning", "statistics"],
        description=(
            "Data science extracts knowledge from data using statistics, computing, and "
            "machine learning, combining mathematics, programming, and domain application."
        ),
        who_its_for=(
            "Students who want to turn data into insight, headed for data science, "
            "analytics, and machine-learning careers."
        ),
    ),
    # ═════════ Graduate academic programs (Engineering) ═════════
    dict(
        slug="ucdavis-computer-science-ms", school=_E, degree_type="masters",
        program_name="Master of Science in Computer Science",
        department="Department of Computer Science", cip="11.0701", duration_months=24,
        keywords=["Computer Science", "graduate", "AI"],
        tuition=_GRAD_ACADEMIC,
        description=(
            "This graduate program advances research and applied work in algorithms, "
            "systems, artificial intelligence, and the theory of computation."
        ),
        who_its_for=(
            "Computing graduates who want research depth or advanced technical skills "
            "before a research or industry career."
        ),
    ),
    dict(
        slug="ucdavis-computer-science-phd", school=_E, degree_type="phd",
        program_name="Doctor of Philosophy in Computer Science",
        department="Department of Computer Science", cip="11.0701", duration_months=60,
        keywords=["Computer Science", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains independent researchers in computer science, from machine "
            "learning and systems to theory, security, and computational biology."
        ),
        who_its_for=(
            "Students aiming at research careers in academia or industry who want to "
            "advance the frontier of computing."
        ),
    ),
    dict(
        slug="ucdavis-electrical-computer-engineering-ms", school=_E, degree_type="masters",
        program_name="Master of Science in Electrical and Computer Engineering",
        department="Department of Electrical and Computer Engineering", cip="14.1001",
        duration_months=24, keywords=["Electrical and Computer Engineering", "graduate"],
        tuition=_GRAD_ACADEMIC,
        description=(
            "This master's advances work in circuits, signal processing, communications, "
            "and embedded and computer systems."
        ),
        who_its_for=(
            "Engineering graduates who want advanced specialization in electrical and "
            "computer systems."
        ),
    ),
    dict(
        slug="ucdavis-electrical-computer-engineering-phd", school=_E, degree_type="phd",
        program_name="Doctor of Philosophy in Electrical and Computer Engineering",
        department="Department of Electrical and Computer Engineering", cip="14.1001",
        duration_months=60, keywords=["Electrical and Computer Engineering", "PhD"],
        funded=True,
        description=(
            "The Ph.D. trains researchers across circuits, communications, signal "
            "processing, photonics, and computer engineering."
        ),
        who_its_for=(
            "Students pursuing research careers in electrical and computer engineering."
        ),
    ),
    dict(
        slug="ucdavis-mechanical-aerospace-engineering-ms", school=_E, degree_type="masters",
        program_name="Master of Science in Mechanical and Aerospace Engineering",
        department="Department of Mechanical and Aerospace Engineering", cip="14.1901",
        duration_months=24, keywords=["Mechanical and Aerospace Engineering", "graduate"],
        tuition=_GRAD_ACADEMIC,
        description=(
            "This master's advances work in solid and fluid mechanics, dynamics and "
            "controls, thermosciences, and aerospace vehicle design."
        ),
        who_its_for=(
            "Mechanical and aerospace graduates who want advanced specialization or a step "
            "toward research."
        ),
    ),
    dict(
        slug="ucdavis-mechanical-aerospace-engineering-phd", school=_E, degree_type="phd",
        program_name="Doctor of Philosophy in Mechanical and Aerospace Engineering",
        department="Department of Mechanical and Aerospace Engineering", cip="14.1901",
        duration_months=60, keywords=["Mechanical and Aerospace Engineering", "PhD"],
        funded=True,
        description=(
            "The Ph.D. trains researchers in mechanics, controls, energy, and aerospace "
            "systems."
        ),
        who_its_for=(
            "Students aiming at research and development careers in mechanical and "
            "aerospace engineering."
        ),
    ),
    dict(
        slug="ucdavis-biomedical-engineering-phd", school=_E, degree_type="phd",
        program_name="Doctor of Philosophy in Biomedical Engineering",
        department="Department of Biomedical Engineering", cip="14.0501", duration_months=60,
        keywords=["Biomedical Engineering", "PhD", "devices"], funded=True,
        description=(
            "The Ph.D. trains researchers in biomedical imaging, devices, biomaterials, and "
            "tissue engineering alongside UC Davis's medical and veterinary schools."
        ),
        who_its_for=(
            "Students who want to research medical technology at the interface of "
            "engineering and biology."
        ),
    ),
    dict(
        slug="ucdavis-chemical-engineering-ms", school=_E, degree_type="masters",
        program_name="Master of Science in Chemical Engineering",
        department="Department of Chemical Engineering", cip="14.0701", duration_months=24,
        keywords=["Chemical Engineering", "graduate"], tuition=_GRAD_ACADEMIC,
        description=(
            "This master's advances work in reaction engineering, transport phenomena, and "
            "process and molecular design."
        ),
        who_its_for=(
            "Chemical engineering graduates who want advanced technical specialization or "
            "research preparation."
        ),
    ),
    dict(
        slug="ucdavis-civil-environmental-engineering-phd", school=_E, degree_type="phd",
        program_name="Doctor of Philosophy in Civil and Environmental Engineering",
        department="Department of Civil and Environmental Engineering", cip="14.0801",
        duration_months=60, keywords=["Civil and Environmental Engineering", "PhD"],
        funded=True,
        description=(
            "The Ph.D. trains researchers in structures, geotechnics, water resources, and "
            "environmental engineering systems."
        ),
        who_its_for=(
            "Students pursuing research in infrastructure, water, and environmental "
            "engineering."
        ),
    ),
    dict(
        slug="ucdavis-materials-science-engineering-ms", school=_E, degree_type="masters",
        program_name="Master of Science in Materials Science and Engineering",
        department="Department of Materials Science and Engineering", cip="14.1801",
        duration_months=24, keywords=["Materials Science and Engineering", "graduate"],
        tuition=_GRAD_ACADEMIC,
        description=(
            "Graduate study here deepens research on microstructure, characterization, and "
            "the design of advanced metals, ceramics, semiconductors, and composites."
        ),
        who_its_for=(
            "Engineering and science graduates who want advanced materials specialization."
        ),
    ),
    dict(
        slug="ucdavis-transportation-technology-policy-ms", school=_E, degree_type="masters",
        program_name="Master of Science in Transportation Technology and Policy",
        department="Institute of Transportation Studies", cip="14.4201", duration_months=24,
        keywords=["Transportation", "policy", "energy"], tuition=_GRAD_ACADEMIC,
        description=(
            "This interdisciplinary program studies transportation systems, energy, and "
            "policy, drawing on UC Davis's nationally recognized Institute of Transportation "
            "Studies."
        ),
        who_its_for=(
            "Students who want to shape sustainable transportation through technology, "
            "planning, and policy."
        ),
    ),
    # ═════════ Graduate academic programs (Letters & Science) ═════════
    dict(
        slug="ucdavis-chemistry-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Chemistry",
        department="Department of Chemistry", cip="40.0501", duration_months=60,
        keywords=["Chemistry", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers across organic, inorganic, physical, analytical, "
            "and chemical-biology research."
        ),
        who_its_for=(
            "Students aiming at research careers in chemistry in academia or industry."
        ),
    ),
    dict(
        slug="ucdavis-physics-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Physics",
        department="Department of Physics and Astronomy", cip="40.0801", duration_months=60,
        keywords=["Physics", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in condensed matter, particle, astro-, and "
            "biological physics."
        ),
        who_its_for=(
            "Students pursuing research careers in physics and related quantitative fields."
        ),
    ),
    dict(
        slug="ucdavis-mathematics-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Mathematics",
        department="Department of Mathematics", cip="27.0101", duration_months=60,
        keywords=["Mathematics", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in pure and applied mathematics — analysis, "
            "algebra, geometry, topology, and applied modeling."
        ),
        who_its_for=(
            "Students aiming at research and teaching careers in the mathematical sciences."
        ),
    ),
    dict(
        slug="ucdavis-statistics-ms", school=_L, degree_type="masters",
        program_name="Master of Science in Statistics",
        department="Department of Statistics", cip="27.0501", duration_months=24,
        keywords=["Statistics", "graduate", "data"], tuition=_GRAD_ACADEMIC,
        description=(
            "This master's advances statistical theory, modeling, and computing for "
            "data-intensive careers and research."
        ),
        who_its_for=(
            "Quantitative graduates who want advanced statistical training for data science "
            "or further study."
        ),
    ),
    dict(
        slug="ucdavis-statistics-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Statistics",
        department="Department of Statistics", cip="27.0501", duration_months=60,
        keywords=["Statistics", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in statistical theory, methodology, and "
            "computation."
        ),
        who_its_for=(
            "Students pursuing research careers in statistics and data science."
        ),
    ),
    dict(
        slug="ucdavis-economics-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Economics",
        department="Department of Economics", cip="45.0601", duration_months=60,
        keywords=["Economics", "PhD", "econometrics"], funded=True,
        description=(
            "The Ph.D. trains research economists in microeconomic theory, econometrics, and "
            "applied and empirical economics."
        ),
        who_its_for=(
            "Students aiming at research careers in academia, government, or industry "
            "economics."
        ),
    ),
    dict(
        slug="ucdavis-psychology-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Psychology",
        department="Department of Psychology", cip="42.0101", duration_months=60,
        keywords=["Psychology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains research psychologists across cognitive, developmental, "
            "social, and biological psychology."
        ),
        who_its_for=(
            "Students pursuing research careers in psychology and the behavioral sciences."
        ),
    ),
    dict(
        slug="ucdavis-sociology-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Sociology",
        department="Department of Sociology", cip="45.1101", duration_months=60,
        keywords=["Sociology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains research sociologists in social structure, inequality, and "
            "quantitative and qualitative methods."
        ),
        who_its_for=(
            "Students pursuing research and teaching careers in sociology and social "
            "science."
        ),
    ),
    dict(
        slug="ucdavis-political-science-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Political Science",
        department="Department of Political Science", cip="45.1001", duration_months=60,
        keywords=["Political Science", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in American and comparative politics, "
            "international relations, and political theory."
        ),
        who_its_for=(
            "Students aiming at research and teaching careers in political science."
        ),
    ),
    dict(
        slug="ucdavis-anthropology-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Anthropology",
        department="Department of Anthropology", cip="45.0201", duration_months=60,
        keywords=["Anthropology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in sociocultural, archaeological, and biological "
            "anthropology."
        ),
        who_its_for=(
            "Students pursuing research careers in anthropology and related fields."
        ),
    ),
    dict(
        slug="ucdavis-history-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in History",
        department="Department of History", cip="54.0101", duration_months=60,
        keywords=["History", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains historians in archival research and historiography across "
            "regions and periods."
        ),
        who_its_for=(
            "Students aiming at research and teaching careers in history."
        ),
    ),
    dict(
        slug="ucdavis-english-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in English",
        department="Department of English", cip="23.0101", duration_months=60,
        keywords=["English", "PhD", "literature"], funded=True,
        description=(
            "The Ph.D. trains scholars in literary history, criticism, and theory across the "
            "Anglophone tradition."
        ),
        who_its_for=(
            "Students pursuing research and teaching careers in literary study."
        ),
    ),
    dict(
        slug="ucdavis-linguistics-phd", school=_L, degree_type="phd",
        program_name="Doctor of Philosophy in Linguistics",
        department="Department of Linguistics", cip="16.0102", duration_months=60,
        keywords=["Linguistics", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in phonology, syntax, semantics, and language "
            "structure and change."
        ),
        who_its_for=(
            "Students aiming at research careers in linguistics and language science."
        ),
    ),
    dict(
        slug="ucdavis-creative-writing-mfa", school=_L, degree_type="masters",
        program_name="Master of Fine Arts in Creative Writing",
        department="Department of English", cip="23.1302", duration_months=24,
        keywords=["Creative Writing", "MFA", "fiction"], tuition=_GRAD_ACADEMIC,
        description=(
            "This studio-and-seminar M.F.A. develops writers of fiction, poetry, and "
            "nonfiction through workshops and close mentorship."
        ),
        who_its_for=(
            "Writers seeking time, mentorship, and a community to complete a "
            "book-length creative project."
        ),
    ),
    # ═════════ Graduate academic programs (Agricultural & Environmental Sciences) ═════════
    dict(
        slug="ucdavis-ecology-phd", school=_C, degree_type="phd",
        program_name="Doctor of Philosophy in Ecology",
        department="Graduate Group in Ecology", cip="26.1301", duration_months=60,
        keywords=["Ecology", "PhD", "conservation"], funded=True,
        description=(
            "Through one of the largest ecology graduate groups in the world, the Ph.D. "
            "trains researchers across population, community, and ecosystem ecology and "
            "conservation."
        ),
        who_its_for=(
            "Students pursuing research careers in ecology, conservation, and environmental "
            "science."
        ),
    ),
    dict(
        slug="ucdavis-animal-biology-phd", school=_C, degree_type="phd",
        program_name="Doctor of Philosophy in Animal Biology",
        department="Graduate Group in Animal Biology", cip="26.0707", duration_months=60,
        keywords=["Animal Biology", "PhD", "physiology"], funded=True,
        description=(
            "The Ph.D. trains researchers in animal physiology, behavior, genetics, and "
            "management across species."
        ),
        who_its_for=(
            "Students pursuing research in animal biology, often alongside the veterinary "
            "and agricultural sciences."
        ),
    ),
    dict(
        slug="ucdavis-nutritional-biology-phd", school=_C, degree_type="phd",
        program_name="Doctor of Philosophy in Nutritional Biology",
        department="Graduate Group in Nutritional Biology", cip="30.1901", duration_months=60,
        keywords=["Nutritional Biology", "PhD", "metabolism"], funded=True,
        description=(
            "The Ph.D. trains researchers in molecular nutrition, metabolism, and human and "
            "animal nutrition."
        ),
        who_its_for=(
            "Students pursuing research careers in nutrition science and metabolic health."
        ),
    ),
    dict(
        slug="ucdavis-food-science-phd", school=_C, degree_type="phd",
        program_name="Doctor of Philosophy in Food Science",
        department="Department of Food Science and Technology", cip="01.1001",
        duration_months=60, keywords=["Food Science", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in food chemistry, microbiology, engineering, and "
            "safety at a leading food-science program."
        ),
        who_its_for=(
            "Students pursuing research and industry-research careers in food science."
        ),
    ),
    dict(
        slug="ucdavis-viticulture-enology-ms", school=_C, degree_type="masters",
        program_name="Master of Science in Viticulture and Enology",
        department="Department of Viticulture and Enology", cip="01.0308", duration_months=24,
        keywords=["Viticulture and Enology", "graduate", "wine"], tuition=_GRAD_ACADEMIC,
        description=(
            "This master's advances the science of grape growing and winemaking, from plant "
            "physiology and soils to fermentation chemistry and microbiology."
        ),
        who_its_for=(
            "Science graduates aiming at research or technical leadership in the wine "
            "industry."
        ),
    ),
    dict(
        slug="ucdavis-agricultural-resource-economics-phd", school=_C, degree_type="phd",
        program_name="Doctor of Philosophy in Agricultural and Resource Economics",
        department="Department of Agricultural and Resource Economics", cip="01.0103",
        duration_months=60, keywords=["Agricultural Economics", "PhD", "resource economics"],
        funded=True,
        description=(
            "The Ph.D. trains researchers in the economics of agriculture, natural "
            "resources, the environment, and development."
        ),
        who_its_for=(
            "Students pursuing research careers in agricultural, resource, and environmental "
            "economics."
        ),
    ),
    dict(
        slug="ucdavis-entomology-phd", school=_C, degree_type="phd",
        program_name="Doctor of Philosophy in Entomology",
        department="Department of Entomology and Nematology", cip="26.0702",
        duration_months=60, keywords=["Entomology", "PhD", "insects"], funded=True,
        description=(
            "The Ph.D. trains researchers in insect biology, ecology, evolution, and pest "
            "management."
        ),
        who_its_for=(
            "Students pursuing research careers in entomology and insect science."
        ),
    ),
    # ═════════ Graduate academic programs (Biological Sciences) ═════════
    dict(
        slug="ucdavis-plant-biology-phd", school=_B, degree_type="phd",
        program_name="Doctor of Philosophy in Plant Biology",
        department="Department of Plant Biology", cip="26.0301", duration_months=60,
        keywords=["Plant Biology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in plant molecular biology, physiology, "
            "development, and genetics."
        ),
        who_its_for=(
            "Students pursuing research careers in plant science and biotechnology."
        ),
    ),
    dict(
        slug="ucdavis-microbiology-phd", school=_B, degree_type="phd",
        program_name="Doctor of Philosophy in Microbiology",
        department="Graduate Group in Microbiology", cip="26.0502", duration_months=60,
        keywords=["Microbiology", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains researchers in microbial physiology, genetics, and the biology "
            "of bacteria and viruses."
        ),
        who_its_for=(
            "Students pursuing research careers in microbiology and infectious disease."
        ),
    ),
    dict(
        slug="ucdavis-neuroscience-phd", school=_B, degree_type="phd",
        program_name="Doctor of Philosophy in Neuroscience",
        department="Graduate Group in Neuroscience", cip="26.1501", duration_months=60,
        keywords=["Neuroscience", "PhD", "brain"], funded=True,
        description=(
            "The Ph.D. trains researchers across molecular, cellular, systems, and cognitive "
            "neuroscience, with ties to the MIND Institute and the medical school."
        ),
        who_its_for=(
            "Students pursuing research careers in neuroscience and brain science."
        ),
    ),
    # ═════════ Graduate academic programs (public-health graduate groups) ═════════
    dict(
        slug="ucdavis-epidemiology-ms", school=_GRAD, degree_type="masters",
        program_name="Master of Science in Epidemiology",
        department="Graduate Group in Epidemiology", cip="26.1309", duration_months=24,
        keywords=["Epidemiology", "graduate", "public health"], tuition=_GRAD_ACADEMIC,
        description=(
            "This program studies the distribution and determinants of disease in "
            "populations, training students in study design and biostatistics."
        ),
        who_its_for=(
            "Students aiming at careers in public health, epidemiology, and population "
            "health research."
        ),
    ),
    dict(
        slug="ucdavis-biostatistics-ms", school=_GRAD, degree_type="masters",
        program_name="Master of Science in Biostatistics",
        department="Graduate Group in Biostatistics", cip="26.1102", duration_months=24,
        keywords=["Biostatistics", "graduate", "health data"], tuition=_GRAD_ACADEMIC,
        description=(
            "This program develops statistical methods for biomedical and health research, "
            "from clinical trials to genomics."
        ),
        who_its_for=(
            "Quantitative students who want to apply statistics to medicine and public "
            "health."
        ),
    ),
    # ═════════ Professional degrees ═════════
    dict(
        slug="ucdavis-mba", school=_GSM, degree_type="masters",
        program_name="Master of Business Administration",
        department="Graduate School of Management", cip="52.0201", duration_months=24,
        keywords=["MBA", "business", "management"], tuition=_MBA_OOS,
        cost_breakdown={"tuition_in_state": _MBA_INSTATE, "tuition_out_of_state": _MBA_OOS},
        cost_note=_MBA_NOTE, cost_source=_MBA_SRC,
        description=(
            "The full-time M.B.A. develops general management skill across finance, "
            "marketing, strategy, and operations, with UC Davis's strengths in technology, "
            "agriculture, food, and sustainability."
        ),
        who_its_for=(
            "Early-career professionals seeking a full-time M.B.A. to move into management, "
            "consulting, or entrepreneurship."
        ),
    ),
    dict(
        slug="ucdavis-professional-accountancy-mpac", school=_GSM, degree_type="masters",
        program_name="Master of Professional Accountancy",
        department="Graduate School of Management", cip="52.0301", duration_months=12,
        keywords=["Accountancy", "MPAc", "CPA"], tuition=_GRAD_ACADEMIC,
        description=(
            "This STEM-designated master's prepares graduates for accounting careers and the "
            "C.P.A. exam, covering financial reporting, audit, tax, and analytics."
        ),
        who_its_for=(
            "Accounting and business graduates pursuing the C.P.A. and careers in public "
            "or corporate accounting."
        ),
    ),
    dict(
        slug="ucdavis-business-analytics-msba", school=_GSM, degree_type="masters",
        program_name="Master of Science in Business Analytics",
        department="Graduate School of Management", cip="52.1301", duration_months=12,
        keywords=["Business Analytics", "MSBA", "data"], tuition=_GRAD_ACADEMIC,
        description=(
            "This STEM-designated master's trains students to turn data into business "
            "decisions, combining statistics, machine learning, and management."
        ),
        who_its_for=(
            "Quantitative graduates who want to launch data-and-analytics careers in "
            "business."
        ),
    ),
    dict(
        slug="ucdavis-juris-doctor-jd", school=_LAW, degree_type="professional",
        program_name="Juris Doctor", department="School of Law", cip="22.0101",
        duration_months=36, keywords=["Law", "JD", "King Hall"], tuition=_JD,
        cost_source=_JD_SRC,
        description=(
            "The J.D. is UC Davis School of Law's professional law degree, known for its "
            "collegial culture and strengths in public-interest, environmental, and "
            "immigration law."
        ),
        who_its_for=(
            "Aspiring lawyers, including those drawn to public-interest and environmental "
            "law and a collaborative law-school culture."
        ),
    ),
    dict(
        slug="ucdavis-master-of-laws-llm", school=_LAW, degree_type="masters",
        program_name="Master of Laws", department="School of Law", cip="22.0202",
        duration_months=12, keywords=["LLM", "law", "international"], tuition=_LLM,
        cost_source=_LLM_SRC,
        description=(
            "The LL.M. gives lawyers — many trained abroad — a year of advanced U.S. legal "
            "study at UC Davis School of Law."
        ),
        who_its_for=(
            "Practicing and internationally trained lawyers seeking advanced U.S. legal "
            "education."
        ),
    ),
    dict(
        slug="ucdavis-doctor-of-medicine-md", school=_MED, degree_type="professional",
        program_name="Doctor of Medicine", department="School of Medicine", cip="51.1201",
        duration_months=48, keywords=["Medicine", "MD", "UC Davis Health"], tuition=_MD,
        cost_source=_MD_SRC,
        description=(
            "The M.D. trains physicians through UC Davis Health, pairing integrated basic "
            "and clinical science with early patient care and strengths in rural and "
            "underserved-community medicine."
        ),
        who_its_for=(
            "Future physicians, including those committed to serving rural and underserved "
            "communities."
        ),
    ),
    dict(
        slug="ucdavis-master-of-public-health-mph", school=_MED, degree_type="masters",
        program_name="Master of Public Health",
        department="Department of Public Health Sciences", cip="51.2201", duration_months=24,
        keywords=["Public Health", "MPH", "epidemiology"], tuition=_MPH_OOS,
        cost_breakdown={"tuition_in_state": _MPH_INSTATE, "tuition_out_of_state": _MPH_OOS},
        cost_note=_MPH_NOTE, cost_source=_MPH_SRC, cost_year="2026-27",
        description=(
            "The M.P.H. trains public-health practitioners in epidemiology, biostatistics, "
            "and prevention, with concentrations in general public health and epidemiology."
        ),
        who_its_for=(
            "Students and clinicians aiming at careers in public health, epidemiology, and "
            "health policy."
        ),
    ),
    dict(
        slug="ucdavis-doctor-of-veterinary-medicine-dvm", school=_VET,
        degree_type="professional",
        program_name="Doctor of Veterinary Medicine",
        department="School of Veterinary Medicine", cip="51.2401", duration_months=48,
        keywords=["Veterinary Medicine", "DVM", "animal health"], tuition=_DVM,
        cost_source=_DVM_SRC,
        description=(
            "The D.V.M. is the professional degree of the UC Davis Weill School of "
            "Veterinary Medicine — ranked No. 1 in the United States — training veterinarians "
            "across companion-animal, livestock, wildlife, and One Health medicine at one of "
            "the largest veterinary teaching hospitals anywhere."
        ),
        who_its_for=(
            "Future veterinarians, including those drawn to research, public health, or "
            "specialized clinical practice."
        ),
    ),
    dict(
        slug="ucdavis-preventive-veterinary-medicine-mpvm", school=_VET,
        degree_type="masters",
        program_name="Master of Preventive Veterinary Medicine",
        department="School of Veterinary Medicine", cip="51.2501", duration_months=12,
        keywords=["Preventive Veterinary Medicine", "MPVM", "epidemiology"],
        omit_tuition_reason=_OMIT_MPVM,
        description=(
            "The M.P.V.M. trains veterinarians and scientists in veterinary epidemiology, "
            "herd and population health, and food safety."
        ),
        who_its_for=(
            "Veterinarians and animal-health scientists focused on population health, "
            "epidemiology, and One Health."
        ),
    ),
    dict(
        slug="ucdavis-master-of-science-nursing-msn", school=_NURS, degree_type="masters",
        program_name="Master of Science in Nursing",
        department="Betty Irene Moore School of Nursing", cip="51.3801", duration_months=18,
        keywords=["Nursing", "MSN", "master's entry"], omit_tuition_reason=_OMIT_NURSING,
        description=(
            "The Master's Entry Program in Nursing prepares non-nursing bachelor's graduates "
            "for registered-nurse licensure and advanced practice through an intensive "
            "prelicensure curriculum."
        ),
        who_its_for=(
            "Career-changers with a bachelor's in another field who want to become "
            "registered nurses and nurse leaders."
        ),
    ),
    dict(
        slug="ucdavis-doctor-nursing-practice-fnp-dnp", school=_NURS, degree_type="phd",
        program_name="Doctor of Nursing Practice — Family Nurse Practitioner",
        department="Betty Irene Moore School of Nursing", cip="51.3805", duration_months=36,
        keywords=["DNP", "Family Nurse Practitioner", "advanced practice"],
        omit_tuition_reason=_OMIT_NURSING,
        description=(
            "This practice doctorate prepares family nurse practitioners to deliver primary "
            "care across the lifespan through a hybrid post-baccalaureate curriculum."
        ),
        who_its_for=(
            "Registered nurses who want to become family nurse practitioners and primary-"
            "care leaders."
        ),
    ),
    dict(
        slug="ucdavis-nursing-science-phd", school=_NURS, degree_type="phd",
        program_name="Doctor of Philosophy in Nursing Science and Health-Care Leadership",
        department="Betty Irene Moore School of Nursing", cip="51.3818", duration_months=60,
        keywords=["Nursing Science", "PhD", "research"], funded=True,
        description=(
            "This research doctorate trains nurse scientists and health-care leaders to "
            "conduct research on health systems, outcomes, and equity."
        ),
        who_its_for=(
            "Nurses and health professionals aiming at research and academic leadership "
            "careers."
        ),
    ),
    # ═════════ School of Education ═════════
    dict(
        slug="ucdavis-education-ma-credential", school=_EDU, degree_type="masters",
        program_name="Master of Arts in Education and Teaching Credential",
        department="School of Education", cip="13.0101", duration_months=18,
        keywords=["Education", "teaching credential", "MA"], tuition=_GRAD_ACADEMIC,
        description=(
            "This program combines a California teaching credential with a Master of Arts in "
            "Education, preparing teachers for elementary and secondary classrooms with a "
            "bilingual option."
        ),
        who_its_for=(
            "Aspiring teachers who want both a credential and a master's degree in one "
            "program."
        ),
    ),
    dict(
        slug="ucdavis-education-phd", school=_EDU, degree_type="phd",
        program_name="Doctor of Philosophy in Education",
        department="School of Education", cip="13.0401", duration_months=60,
        keywords=["Education", "PhD", "research"], funded=True,
        description=(
            "The Ph.D. trains education researchers in learning, equity, language, and "
            "policy across the lifespan."
        ),
        who_its_for=(
            "Students pursuing research and academic careers in education."
        ),
    ),
    dict(
        slug="ucdavis-educational-leadership-edd", school=_EDU, degree_type="phd",
        program_name="Doctor of Education in Educational Leadership",
        department="School of Education", cip="13.0401", duration_months=36,
        keywords=["Educational Leadership", "EdD", "CANDEL"], omit_tuition_reason=_OMIT_EDD,
        description=(
            "The CANDEL Ed.D. is a practice doctorate for working education leaders, "
            "combining applied research with leadership in schools, colleges, and agencies."
        ),
        who_its_for=(
            "Experienced education professionals moving into senior leadership who want an "
            "applied doctorate."
        ),
    ),
]

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
        "cost_breakdown": r.get("cost_breakdown"),
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
    _seenk: set = set()
    _dupk = [k for k in _name_keys if k in _seenk or _seenk.add(k)]
    raise RuntimeError(f"duplicate (program_name, degree_type) in UC Davis catalog: {_dupk}")

# ── Concentrations / tracks (belong on the program, not as separate rows) ──
_TRACKS_BY_SLUG: dict[str, list[str]] = {
    "ucdavis-marine-coastal-science-bs": [
        "Coastal Environmental Processes and Marine Chemistry",
        "Oceans and the Earth System",
        "Marine Ecology and Organismal Biology",
    ],
    "ucdavis-political-science-ba": [
        "American Politics",
        "Comparative Politics",
        "International Relations",
        "Political Theory",
        "Public Service",
    ],
    "ucdavis-sociology-ba": ["General Sociology", "Organizational Studies"],
    "ucdavis-master-of-public-health-mph": ["General Public Health", "Epidemiology"],
}

# ── Outcomes (institution-wide; UC Davis publishes outcomes per-college, not per-program) ──
_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 80838,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (UC Davis, UNITID 110644)",
    "source_url": "https://collegescorecard.ed.gov/school/?110644",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "UC Application",
        "Personal Insight Questions (UC essays)",
        "Secondary-school transcript / academic record",
        "No SAT or ACT — UC is test-blind (scores are not considered)",
    ],
    "deadlines": {
        "application_period": "October 1 – December 2 (UC systemwide)",
    },
    "source": "https://www.ucdavis.edu/admissions",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online graduate application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose and personal history statement",
        "English-proficiency scores where required",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://grad.ucdavis.edu/admissions",
}
_REQ_MBA = {
    "materials": [
        "Graduate School of Management application + essays",
        "GMAT or GRE score (waivers considered)",
        "Undergraduate transcripts",
        "Letters of recommendation",
        "Resume + interview",
    ],
    "deadlines": {"note": "Rounds; see the Graduate School of Management admissions page."},
    "source": "https://gsm.ucdavis.edu/full-time-mba/admissions",
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
    "source": "https://law.ucdavis.edu/admissions",
}
_REQ_MED = {
    "materials": [
        "AMCAS application + UC Davis secondary",
        "MCAT score",
        "Undergraduate transcripts",
        "Letters of recommendation",
        "Interviews as required",
    ],
    "deadlines": {"primary": "AMCAS deadline (see admissions site)"},
    "source": "https://health.ucdavis.edu/medschool/admissions/",
}
_REQ_DVM = {
    "materials": [
        "VMCAS application + UC Davis supplemental",
        "Prerequisite coursework",
        "Veterinary and animal experience",
        "Letters of recommendation",
        "Interviews as required",
    ],
    "deadlines": {"primary": "VMCAS deadline (see admissions site)"},
    "source": "https://www.vetmed.ucdavis.edu/education/dvm-program/admissions",
}


def _requirements_for(spec: dict) -> dict:
    school = spec["school"]
    slug = spec["slug"]
    if slug == "ucdavis-doctor-of-veterinary-medicine-dvm":
        return dict(_REQ_DVM)
    if school == _LAW and spec["degree_type"] == "professional":
        return dict(_REQ_LAW)
    if school == _MED and spec["degree_type"] == "professional":
        return dict(_REQ_MED)
    if spec["slug"] == "ucdavis-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


# ── External reviews — MBAn shape; gathered → summarized → cited (cautions included) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "ucdavis-doctor-of-veterinary-medicine-dvm": {
        "summary": (
            "The UC Davis Weill School of Veterinary Medicine is the most highly regarded "
            "veterinary school in the United States — ranked No. 1 nationally by U.S. News "
            "and among the very best in the world by QS — and its teaching hospital is one "
            "of the largest anywhere, giving D.V.M. students exceptional clinical breadth "
            "across companion animals, livestock, wildlife, and research."
        ),
        "themes": [
            {
                "label": "Top-ranked program",
                "sentiment": "positive",
                "detail": (
                    "Ranked No. 1 in the U.S. by U.S. News for veterinary medicine and "
                    "consistently top-ranked in the world by QS."
                ),
            },
            {
                "label": "Exceptional clinical training",
                "sentiment": "positive",
                "detail": (
                    "The UC Davis veterinary teaching hospital — among the largest "
                    "anywhere — provides broad caseload and specialty exposure."
                ),
            },
            {
                "label": "Research and One Health strength",
                "sentiment": "positive",
                "detail": (
                    "Deep research and a One Health focus connect animal, human, and "
                    "environmental health."
                ),
            },
            {
                "label": "Highly competitive admission",
                "sentiment": "caution",
                "detail": (
                    "As the top-ranked program, admission is extremely selective with a "
                    "limited class size."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Veterinary school is a significant financial commitment, and "
                    "non-resident tuition is higher; scholarships are available but debt "
                    "financing is common."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Veterinary Schools (UC Davis)",
                "url": "https://www.usnews.com/best-graduate-schools/top-veterinary-schools/uc-davis-06013",
            },
            {
                "label": "UC Davis School of Veterinary Medicine — Rankings & News",
                "url": "https://www.vetmed.ucdavis.edu/about/rankings",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official school information, not individual verbatim reviews."
        ),
    },
    "ucdavis-mba": {
        "summary": (
            "The UC Davis Graduate School of Management full-time M.B.A. is a small, "
            "highly personalized program valued for close faculty access and individualized "
            "career coaching, with particular strength in technology, agriculture and food, "
            "and sustainability given UC Davis's research base. It is regularly ranked among "
            "the better public M.B.A. programs."
        ),
        "themes": [
            {
                "label": "Small, personalized cohort",
                "sentiment": "positive",
                "detail": (
                    "A small class size means close faculty contact and one-on-one career "
                    "support."
                ),
            },
            {
                "label": "Sector strengths",
                "sentiment": "positive",
                "detail": (
                    "Strong ties to technology, agriculture and food, and sustainability "
                    "through UC Davis's research strengths."
                ),
            },
            {
                "label": "Proximity to the Bay Area and Sacramento",
                "sentiment": "positive",
                "detail": (
                    "Located between the Bay Area tech economy and the state capital, with "
                    "recruiting access to both."
                ),
            },
            {
                "label": "Smaller alumni network than larger programs",
                "sentiment": "mixed",
                "detail": (
                    "The intimate program size means a smaller alumni base than at the "
                    "largest M.B.A. programs."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "A full-time M.B.A. carries significant tuition and opportunity cost; "
                    "scholarships are available."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Business Schools (UC Davis)",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-california-davis-01313",
            },
            {
                "label": "UC Davis Graduate School of Management — Full-Time M.B.A.",
                "url": "https://gsm.ucdavis.edu/full-time-mba",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official school information, not individual verbatim reviews."
        ),
    },
    "ucdavis-juris-doctor-jd": {
        "summary": (
            "UC Davis School of Law (King Hall) is a well-regarded public law school known "
            "for an unusually collegial, public-service-minded culture and recognized "
            "strengths in environmental, immigration, and public-interest law. It is "
            "consistently ranked among the better public law schools by U.S. News."
        ),
        "themes": [
            {
                "label": "Collegial culture",
                "sentiment": "positive",
                "detail": (
                    "King Hall is widely described as collaborative and supportive rather "
                    "than cut-throat."
                ),
            },
            {
                "label": "Public-interest & environmental strengths",
                "sentiment": "positive",
                "detail": (
                    "Recognized programs in environmental, immigration, and public-interest "
                    "law, with active clinics."
                ),
            },
            {
                "label": "California legal market access",
                "sentiment": "positive",
                "detail": (
                    "Strong placement in California, including the Sacramento and Bay Area "
                    "legal and government markets."
                ),
            },
            {
                "label": "Cost and selectivity",
                "sentiment": "caution",
                "detail": (
                    "Tuition is substantial and admission is competitive; outcomes are "
                    "strong but the financial commitment is real."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Law Schools (UC Davis)",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-california-davis-03013",
            },
            {
                "label": "UC Davis School of Law — Employment Data (ABA disclosures)",
                "url": "https://law.ucdavis.edu/careers/employment-statistics",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official ABA employment disclosures, not individual verbatim reviews."
        ),
    },
    "ucdavis-doctor-of-medicine-md": {
        "summary": (
            "The UC Davis School of Medicine is recognized for primary care and for its "
            "commitment to rural and underserved communities, training physicians through "
            "UC Davis Health, an academic medical center with an NCI-designated "
            "comprehensive cancer center and the MIND Institute."
        ),
        "themes": [
            {
                "label": "Primary care & community strength",
                "sentiment": "positive",
                "detail": (
                    "Highly ranked for primary care, with programs focused on rural and "
                    "underserved-community medicine."
                ),
            },
            {
                "label": "Academic medical center",
                "sentiment": "positive",
                "detail": (
                    "Training at UC Davis Health, including a comprehensive cancer center "
                    "and the MIND Institute for neurodevelopment."
                ),
            },
            {
                "label": "Research breadth",
                "sentiment": "positive",
                "detail": (
                    "Access to wide-ranging biomedical and translational research."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Admission to medical school is highly competitive, with a limited "
                    "class size."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Best Medical Schools (UC Davis)",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-california-davis-04013",
            },
            {
                "label": "UC Davis School of Medicine",
                "url": "https://health.ucdavis.edu/medschool/",
            },
        ],
        "disclaimer": (
            "Themes are aggregated and paraphrased from public third-party coverage and "
            "official school information, not individual verbatim reviews."
        ),
    },
}


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


def apply(session: Session) -> bool:
    """Enrich UC Davis to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UC Davis is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1905
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.ucdavis.edu"
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
    # PUBLIC scalar = NON-RESIDENT (out-of-state); breakdown keeps BOTH rates (run-83 rule).
    return {
        "tuition_usd": _UG_OOS,
        "avg_net_price": _UG_NET,
        "breakdown": {
            "tuition": _UG_OOS,
            "tuition_in_state": _UG_INSTATE,
            "tuition_out_of_state": _UG_OOS,
        },
        "funded": False,
        "note": (
            "UC Davis is a public university with two published undergraduate stickers: "
            "$16,774 for California residents and $50,974 for non-residents (2024-25, "
            "tuition + fees). The scalar shown is the non-resident rate — the "
            "broadly-correct budget input for a national and international applicant pool; "
            "the resident rate is preserved in the breakdown. The College Scorecard average "
            "net price after aid is about $14,700."
        ),
        "source": _UG_SRC[0],
        "source_url": _UG_SRC[1],
        "year": "2024-25",
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
            p.tuition = _UG_OOS
            p.cost_data = _undergrad_cost()
        elif spec.get("tuition") is not None:
            p.tuition = spec["tuition"]
            p.cost_data = {
                "tuition_usd": spec["tuition"],
                "funded": False,
                "note": spec.get("cost_note") or _GRAD_ACADEMIC_NOTE,
                "source": (spec.get("cost_source") or _UCOP_SRC)[0],
                "source_url": (spec.get("cost_source") or _UCOP_SRC)[1],
                "year": spec.get("cost_year") or "2025-26",
            }
            if spec.get("cost_breakdown"):
                p.cost_data["breakdown"] = spec["cost_breakdown"]
        elif spec.get("funded"):
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": _FUNDED_PHD_NOTE,
                "source": _UCOP_SRC[0],
                "source_url": _UCOP_SRC[1],
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": spec.get("omit_tuition_reason", (
                    "A verified per-program annual tuition figure is omitted here rather "
                    "than estimated; see the program's official cost page."
                )),
                "source": _UCOP_SRC[0],
                "source_url": _UCOP_SRC[1],
            }
        p.cip_code = spec["cip"]
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        spec_with_tracks = dict(spec)
        spec_with_tracks["tracks"] = _TRACKS_BY_SLUG.get(slug)
        outcomes["_standard"] = _program_standard(spec_with_tracks)
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
