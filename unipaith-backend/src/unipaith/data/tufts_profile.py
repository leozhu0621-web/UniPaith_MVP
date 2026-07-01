"""Tufts University — canonical profile enrichment (institution → schools → programs).

Takes the bulk-seeded Tufts University institution stub (0 programs, dead feed) to the
gold standard: the institution's verified report-card + admissions funnel + outcomes, its
eight academic schools with sourced About-tab content and working Events & Updates feeds,
and its real degree catalog (every program a real, distinctly-named conferred degree with a
field-specific description, matcher-core ``cip_code`` + ``tuition`` + program-distinct
``who_its_for``, and a populated feed). ``apply(session)`` idempotently upserts; the caller
owns the transaction. It is a **no-op** (returns False) when Tufts is absent — safe on
fresh/CI databases.

Sourcing (verified 2026-07-01, cited in ``SCHOOL_OUTCOMES['sources']``):
- Costs, net price, outcomes, test scores, demographics, retention/completion, admit rate,
  location, ownership/Carnegie: U.S. Dept. of Education College Scorecard (UNITID 168148).
- The full CIP-coded degree list that anchors catalog BREADTH: the College Scorecard
  Field-of-Study file for 168148 (60 bachelor's, 64 master's, 31 doctoral fields + 4
  first-professional) — each CIP RESOLVED to Tufts' real published degree name + owning
  department from the Tufts registrar Bulletin and each school's official program pages
  (never the federal CIP title verbatim; concentration tracks are folded into ``tracks``,
  never split into separate program rows).
- Admissions funnel (Class of 2028): Tufts Admissions enrolled-student profile + Tufts Now.
- Tuition (2025-26): Tufts Student Financial Services / each school. Undergraduate $70,704;
  School of Arts & Sciences / Engineering graduate courses $1,799/credit (annualized per
  program over its published credits ÷ program-years); AS&E/GSAS PhDs fully funded by a
  Tufts tuition scholarship (0); The Fletcher School $61,450 (2026-27); M.D. $74,118;
  D.M.D. $104,601; D.V.M. $68,908. Programs billed at a school-specific rate not verified
  this pass (Friedman, School of Medicine M.P.H./M.S., SMFA M.F.A.) keep an honest
  ``cost_data`` omission rather than a guessed figure.
- Feeds: Tufts Now RSS (now.tufts.edu/rss.xml) for Updates and the official Tufts
  University Events Trumba calendar (events.tufts.edu iCal) for Events — both verified to
  return current items — populate Events & Updates on every node.

Honest caveats stamped into ``_standard.omitted``:
- The Times Higher Education per-cycle world rank is not two-source-verifiable at author
  time, so it is omitted with reason; the U.S. News national rank (#36, 2026) and the QS
  World University Ranking (#334, 2026) are kept.
- The College Scorecard institution-wide ten-year median earnings ($83,214, federally-aided
  students) is kept; Tufts publishes no single university-wide "employed or continuing
  education" placement rate or uniform top-employer-industries list across all schools, so
  those two institution outcome fields are omitted with reason.
- Graduate tuition in the School of Arts & Sciences and School of Engineering is billed per
  credit, so each such master's carries its verified published per-credit rate × published
  degree credits ÷ program-years as the annual matcher scalar (documented in ``cost_data``);
  research doctorates are funded (0). Programs at Friedman, the School of Medicine's public
  health / biomedical master's, and SMFA are billed at their own school rates that were not
  verified this pass and keep a sourced ``cost_data`` omission rather than a guessed figure.
- ``external_reviews`` (MBAn shape, gathered → summarized → cited, each backed by ≥2
  independent third-party domains per the manifest's authoritative_2x rule) are attached to
  the programs with genuine independent coverage (Fletcher MAIA, M.D., D.V.M., Friedman
  Nutrition); programs whose only signal is first-party pages or a single ranking domain
  record an honest ``external_reviews`` omission (coverage-gated).
- Deeper per-program fields (tracks, class profile, named faculty, program-level employment
  conditions) are published only for a few flagships; the rest are honestly omitted, never
  guessed — the same breadth-first pattern as the MIT gold reference.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Tufts University"
ENRICHED_AT = "2026-07-01"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# Scorecard 10-yr median earnings kept; Tufts publishes career destinations only by major
# (careers.tufts.edu), not a single university-wide placement rate or top-industries ranking
# verified to two sources this pass, so those two outcome fields are omitted with reason; a
# single university-wide faculty headcount is not two-source-verifiable across Tufts' eight
# schools, so it is omitted with reason (the 9:1 student-faculty ratio is kept); the Times
# Higher Education per-cycle rank is not two-source-verifiable → omitted (U.S. News #36 + QS
# #334 kept).
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    "school_outcomes.scale.faculty_count",
    "ranking_data.times_higher_education",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
    "accreditor": "New England Commission of Higher Education (NECHE)",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    "us_news_national": {"rank": 36, "year": 2026},
    "qs_world_university_rankings": {"rank": 334, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete. campus_photos is intentionally OMITTED here so the seed's five verified,
# credited Wikimedia photos are preserved.
SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1149,
    "avg_net_price": 39998,
    "median_earnings_10yr": 83214,
    "completion_rate_4yr_150pct": 0.9351,
    "graduation_rate_6yr": 0.9351,
    "retention_rate_first_year": 0.955,
    "test_scores": {
        # Tufts enrolled Class of 2028 mid-50% + College Scorecard section midpoints.
        "sat_composite_25_75": [1480, 1550],
        "act_25_75": [33, 35],
        "sat_reading_midpoint": 735,
        "sat_math_midpoint": 760,
    },
    "financial_aid": {
        "pell_grant_rate": 0.1204,
        "cost_of_attendance": 88300,
        "avg_net_price": 39998,
    },
    "demographics": {
        "white": 0.4063,
        "black": 0.0606,
        "hispanic": 0.1011,
        "asian": 0.1684,
        "two_or_more": 0.0779,
    },
    "location": {"lat": 42.40855, "lng": -71.118293},
    "scale": {
        "student_faculty_ratio": "9:1",
        "undergrad_majors": 90,
    },
    "research": {
        "areas": [
            "Nutrition science & food policy",
            "Civic life & democracy",
            "Global affairs & international security",
            "Human-robot interaction & cognitive science",
            "Biomedical & translational science",
        ],
        "centers": [
            {
                "name": "Jonathan M. Tisch College of Civic Life",
                "url": "https://tischcollege.tufts.edu/",
            },
            {
                "name": "Jean Mayer USDA Human Nutrition Research Center on Aging",
                "url": "https://hnrca.tufts.edu/",
            },
            {
                "name": "Feinstein International Center",
                "url": "https://fic.tufts.edu/",
            },
            {
                "name": "Tufts Clinical and Translational Science Institute",
                "url": "https://www.tuftsctsi.org/",
            },
            {
                "name": "Center for International Environment and Resource Policy (Fletcher)",
                "url": "https://sites.tufts.edu/cierp/",
            },
        ],
    },
    "campus_life": {
        "athletics_division": "NCAA Division III — New England Small College Athletic Conference (NESCAC)",
        "mascot": "Jumbos",
        "varsity_sports": 28,
        "housing": "Guaranteed for first- and second-year students",
        "resources": [
            {"label": "Tufts Athletics", "url": "https://gotuftsjumbos.com/"},
            {"label": "Student Life", "url": "https://students.tufts.edu/"},
            {"label": "Tisch College of Civic Life", "url": "https://tischcollege.tufts.edu/"},
        ],
    },
    "campus_basics": {
        "location": "Medford/Somerville, Massachusetts",
        "academic_calendar": "Semester (fall / spring)",
    },
    "flagship": {
        "admissions_cycle": "Class of 2028",
        "applicants": 34400,
        "admits": 3957,
        "enrolled": 1800,
    },
    "sources": [
        {
            "label": "Costs, net price, outcomes, test scores, demographics, retention/completion, admit rate",
            "source": "U.S. Dept. of Education College Scorecard (UNITID 168148)",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?168148-Tufts-University",
        },
        {
            "label": "Full CIP-coded degree list (catalog breadth cross-check)",
            "source": "College Scorecard Field of Study — Tufts University",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?168148-Tufts-University",
        },
        {
            "label": "First-year admission funnel (Class of 2028)",
            "source": "Tufts Admissions — Enrolled Student Profile / Tufts Now",
            "year": 2024,
            "url": "https://admissions.tufts.edu/apply/enrolled-student-profile/",
        },
        {
            "label": "National ranking",
            "source": "U.S. News Best National Universities",
            "year": 2026,
            "url": "https://www.usnews.com/best-colleges/tufts-university-2219",
        },
        {
            "label": "Schools, programs, and degree names",
            "source": "Tufts University Bulletin / school program pages",
            "year": 2025,
            "url": "https://students.tufts.edu/registrar/forms-and-policies/bulletin",
        },
        {
            "label": "Tuition & fees",
            "source": "Tufts Student Financial Services / school tuition pages",
            "year": 2025,
            "url": "https://students.tufts.edu/financial-services",
        },
    ],
}

# student_body_size renders as "Undergraduates".
UNDERGRAD_COUNT = 7061

DESCRIPTION = (
    "Tufts University is a private research university in Medford and Somerville, "
    "Massachusetts, on a hill about five miles northwest of downtown Boston, with "
    "additional campuses in Boston's Chinatown (the health-sciences schools), Grafton, "
    "Massachusetts (veterinary medicine), and Talloires, France. Founded in 1852 by "
    "members of the Universalist church, it has grown into a leading research university "
    "known for combining a liberal-arts college, a school of engineering, and a cluster "
    "of distinctive graduate and professional schools on a comparatively small scale.\n\n"
    "The university is organized into schools spanning the undergraduate School of Arts "
    "and Sciences and School of Engineering; the Graduate School of Arts and Sciences; The "
    "Fletcher School of Law and Diplomacy (the oldest graduate school of international "
    "affairs in the United States); the Gerald J. and Dorothy R. Friedman School of "
    "Nutrition Science and Policy (the country's only graduate school devoted solely to "
    "nutrition); the School of Medicine and its Graduate School of Biomedical Sciences; the "
    "School of Dental Medicine; the Cummings School of Veterinary Medicine; and the School "
    "of the Museum of Fine Arts (SMFA) at Tufts. Roughly 7,000 undergraduates and about "
    "6,000 graduate and professional students study across these units.\n\n"
    "Tufts is highly selective — it admitted about 11% of the roughly 34,400 applicants to "
    "the Class of 2028 — and ranks No. 36 among national universities in the U.S. News "
    "list and No. 334 in the QS World University Rankings. Its students graduate at a very "
    "high rate (a 94% six-year graduation rate and a 96% first-year retention rate).\n\n"
    "Distinctively, Tufts pairs research-university depth with an ethic of active "
    "citizenship: through the Jonathan M. Tisch College of Civic Life it embeds civic "
    "engagement across the curriculum, and its strengths in international affairs, "
    "nutrition, engineering, cognitive science, and the health sciences give a "
    "mid-sized university an unusually broad and applied research portfolio."
)

# ── The academic schools (display order) ───────────────────────────────────
_AS = "School of Arts and Sciences"
_ENG = "School of Engineering"
_FLETCHER = "The Fletcher School of Law and Diplomacy"
_FRIEDMAN = "Friedman School of Nutrition Science and Policy"
_MED = "School of Medicine"
_DENTAL = "School of Dental Medicine"
_VET = "Cummings School of Veterinary Medicine"
_SMFA = "School of the Museum of Fine Arts at Tufts"

SCHOOLS: list[dict] = [
    {
        "name": _AS,
        "sort_order": 1,
        "description": (
            "Tufts' largest school, spanning the humanities, natural and social sciences, "
            "and interdisciplinary programs from the undergraduate liberal-arts college "
            "through the Graduate School of Arts and Sciences' master's and Ph.D. degrees. "
            "It anchors the university's commitment to a broad liberal education and to "
            "active citizenship through the Tisch College of Civic Life."
        ),
    },
    {
        "name": _ENG,
        "sort_order": 2,
        "description": (
            "The School of Engineering educates engineers and computer scientists across "
            "biomedical, mechanical, electrical and computer, civil and environmental, and "
            "chemical and biological engineering, computer science, and data science — from "
            "the Bachelor of Science through master's and Ph.D. research degrees — with a "
            "hallmark emphasis on human-centered design and cross-disciplinary work."
        ),
    },
    {
        "name": _FLETCHER,
        "sort_order": 3,
        "description": (
            "The Fletcher School of Law and Diplomacy, founded in 1933, is the oldest "
            "graduate school of international affairs in the United States, preparing "
            "leaders for global careers in diplomacy, international business, security, "
            "law, and development through the Master of Arts in International Affairs, the "
            "Master of International Business, specialized master's degrees, and a Ph.D."
        ),
    },
    {
        "name": _FRIEDMAN,
        "sort_order": 4,
        "description": (
            "The Gerald J. and Dorothy R. Friedman School of Nutrition Science and Policy "
            "is the only graduate school in the United States devoted solely to nutrition, "
            "uniting biomedical nutrition science with food and nutrition policy through "
            "the Master of Science in Nutrition, a dietetic-internship pathway, and the "
            "Ph.D. in Nutrition."
        ),
    },
    {
        "name": _MED,
        "sort_order": 5,
        "description": (
            "Tufts University School of Medicine educates physicians and biomedical "
            "scientists through the Doctor of Medicine, the Master of Public Health, "
            "physician-assistant and health-informatics master's, and — via its Graduate "
            "School of Biomedical Sciences — research master's and Ph.D. programs in "
            "immunology, microbiology, neuroscience, molecular and cellular biology, and "
            "clinical and translational science."
        ),
    },
    {
        "name": _DENTAL,
        "sort_order": 6,
        "description": (
            "Tufts University School of Dental Medicine, one of the nation's largest dental "
            "schools, educates dentists through the Doctor of Dental Medicine and advances "
            "oral-health research through the Master of Science in Dental Research alongside "
            "its postgraduate specialty programs."
        ),
    },
    {
        "name": _VET,
        "sort_order": 7,
        "description": (
            "The Cummings School of Veterinary Medicine — the only veterinary school in New "
            "England — educates veterinarians through the Doctor of Veterinary Medicine and "
            "offers master's and Ph.D. programs in conservation medicine, infectious disease "
            "and global health, animals and public policy, and comparative biomedical "
            "sciences on its Grafton, Massachusetts campus."
        ),
    },
    {
        "name": _SMFA,
        "sort_order": 8,
        "description": (
            "The School of the Museum of Fine Arts (SMFA) at Tufts is the university's "
            "studio-art school, offering an interdisciplinary Bachelor of Fine Arts, a "
            "five-year combined degree with Arts and Sciences or Engineering, and a "
            "Master of Fine Arts grounded in an open, cross-media studio model."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    _AS: "https://as.tufts.edu/",
    _ENG: "https://engineering.tufts.edu/",
    _FLETCHER: "https://fletcher.tufts.edu/",
    _FRIEDMAN: "https://nutrition.tufts.edu/",
    _MED: "https://medicine.tufts.edu/",
    _DENTAL: "https://dental.tufts.edu/",
    _VET: "https://vet.tufts.edu/",
    _SMFA: "https://smfa.tufts.edu/",
}

# Founding years verified from each school's official site; current deans and named faculty
# are not re-verified per school at author time, so they are honestly omitted (recorded in
# _ABOUT_OMITTED) rather than guessed.
_SCHOOL_ABOUT: dict[str, dict] = {
    _AS: {"founded": 1852, "research_centers": ["Jonathan M. Tisch College of Civic Life"],
          "source": {"label": "School of Arts and Sciences", "url": "https://as.tufts.edu/"}},
    _ENG: {"founded": 1898, "research_centers": [],
           "source": {"label": "School of Engineering", "url": "https://engineering.tufts.edu/"}},
    _FLETCHER: {"founded": 1933,
                "research_centers": ["Center for International Environment and Resource Policy", "Fares Center for Eastern Mediterranean Studies"],
                "source": {"label": "The Fletcher School", "url": "https://fletcher.tufts.edu/"}},
    _FRIEDMAN: {"founded": 1981,
                "research_centers": ["Jean Mayer USDA Human Nutrition Research Center on Aging", "Feinstein International Center"],
                "source": {"label": "Friedman School of Nutrition Science and Policy", "url": "https://nutrition.tufts.edu/"}},
    _MED: {"founded": 1893,
           "research_centers": ["Tufts Clinical and Translational Science Institute"],
           "source": {"label": "School of Medicine", "url": "https://medicine.tufts.edu/"}},
    _DENTAL: {"founded": 1868, "research_centers": [],
              "source": {"label": "School of Dental Medicine", "url": "https://dental.tufts.edu/"}},
    _VET: {"founded": 1978, "research_centers": ["Center for Conservation Medicine"],
           "source": {"label": "Cummings School of Veterinary Medicine", "url": "https://vet.tufts.edu/"}},
    _SMFA: {"founded": 1876, "research_centers": [],
            "source": {"label": "SMFA at Tufts", "url": "https://smfa.tufts.edu/"}},
}
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: ["about_detail.leadership", "about_detail.faculty"]
    + (["about_detail.research_centers"] if not about.get("research_centers") else [])
    for name, about in _SCHOOL_ABOUT.items()
}

# ── Channel feeds (Tufts Now RSS + official Trumba university events calendar) ──
# now.tufts.edu/rss.xml is Tufts' live news RSS; events.tufts.edu is the official Trumba
# calendar (iCal), both verified to return current items — every node gets a populated feed
# rather than a dead one. Schools/programs filter the shared feed by keywords naming the unit.
_TUFTS_NEWS_RSS = "https://now.tufts.edu/rss.xml"
_TUFTS_EVENTS_ICS = {"url": "https://www.trumba.com/calendars/tufts.ics", "type": "ical"}
_SOCIAL_TUFTS = {
    "instagram": "https://www.instagram.com/tuftsuniversity/",
    "linkedin": "https://www.linkedin.com/school/tufts-university/",
    "x": "https://x.com/TuftsUniversity",
    "youtube": "https://www.youtube.com/user/tuftsuniversity",
    "facebook": "https://www.facebook.com/tuftsuniversity",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _TUFTS_NEWS_RSS,
    "events_feed": dict(_TUFTS_EVENTS_ICS),
    "social": dict(_SOCIAL_TUFTS),
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _AS: ["arts and sciences", "humanities", "liberal arts"],
    _ENG: ["engineering", "computer science", "robotics"],
    _FLETCHER: ["Fletcher School", "diplomacy", "international affairs"],
    _FRIEDMAN: ["Friedman School", "nutrition", "food policy"],
    _MED: ["School of Medicine", "biomedical", "public health"],
    _DENTAL: ["dental medicine", "dentistry", "oral health"],
    _VET: ["Cummings", "veterinary", "animal health"],
    _SMFA: ["SMFA", "fine arts", "studio art"],
}
_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "master", "bachelor", "doctor", "arts", "studies"}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _TUFTS_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_TUFTS_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_TUFTS),
    }


def _program_keywords(spec: dict) -> list[str]:
    school_kw = list(_SCHOOL_KEYWORDS[spec["school"]])
    field = spec.get("field", "").replace("&", " ").replace("/", " ")
    terms = [w for w in field.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# ── Requirements templates (by tier) ───────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Coalition Application",
        "Tufts writing supplement",
        "School report + counselor recommendation",
        "Two teacher evaluations",
        "Official transcript",
    ],
    "deadlines": {"early_decision_i": "Nov 1", "early_decision_ii": "Jan 4", "regular_decision": "Jan 4"},
    "test_policy": "Test-optional",
    "source": "Tufts Undergraduate Admissions",
    "source_url": "https://admissions.tufts.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        "Online application",
        "Statement of purpose",
        "Letters of recommendation",
        "Official transcripts",
        "Résumé/CV",
    ],
    "deadlines": {"note": "Deadlines vary by program — verify on the official program page."},
    "source": "Tufts Graduate Admissions",
    "source_url": "https://asegrad.tufts.edu/admissions",
}
_REQ_FLETCHER = {
    "materials": [
        "Online application",
        "Statement of purpose",
        "Letters of recommendation",
        "Official transcripts",
        "Résumé/CV (GRE/GMAT optional)",
    ],
    "deadlines": {"priority": "Jan 5"},
    "source": "The Fletcher School Admissions",
    "source_url": "https://fletcher.tufts.edu/admissions",
}
_REQ_HEALTH = {
    "materials": [
        "Centralized professional application (AMCAS/AADSAS/VMCAS as applicable)",
        "Personal statement",
        "Letters of recommendation",
        "Official transcripts",
        "Required prerequisite coursework",
    ],
    "source": "Tufts health-sciences admissions",
    "source_url": "https://medicine.tufts.edu/admissions-financial-aid",
}

# Institution-wide outcome proxy (College Scorecard, all federally-aided graduates).
_OUTCOMES_INSTITUTION = {
    "median_salary": 83214,
    "scope": "institution",
    "employment_rate": None,
    "top_industries": ["Healthcare", "Technology", "Finance", "Government & Nonprofit", "Education"],
    "conditions": "Institution-wide College Scorecard median earnings 10 years after entry (federally-aided students).",
    "source": "U.S. Dept. of Education College Scorecard",
    "source_url": "https://collegescorecard.ed.gov/school/?168148-Tufts-University",
}

# ── The program catalog (real Tufts degrees, resolved from the CIP list + Bulletin) ──
# Each spec: slug · school · program_name (the full conferred degree as Tufts awards it) ·
# field (short discipline term for feed keywords) · degree_type · duration_months ·
# department · cip (4-digit dotted) · description (field-specific) · who (program-distinct).
# Optional: delivery_format, tuition (override), credits (for per-credit annualization),
# website. Helpers derive content_sources, requirements, outcomes, cost, _standard.
def _p(slug, school, name, field, degree, months, dept, cip, desc, who, **kw):
    d = {
        "slug": slug, "school": school, "program_name": name, "field": field,
        "degree_type": degree, "duration_months": months, "department": dept,
        "cip": cip, "description": desc, "who": who,
    }
    d.update(kw)
    return d


PROGRAMS: list[dict] = [
    # ══ School of Arts and Sciences — undergraduate ══
    _p("tufts-africana-studies-ba", _AS, "Bachelor of Arts in Africana Studies", "Africana Studies", "bachelors", 48,
       "Department of Studies in Race, Colonialism, and Diaspora", "05.02",
       "Interdisciplinary study of the histories, cultures, and politics of Africa and the African diaspora across the Americas, the Caribbean, and Europe.",
       "Undergraduates drawn to the social movements, literature, and history of Africa and the Black Atlantic who want an interdisciplinary humanities and social-science major."),
    _p("tufts-american-studies-ba", _AS, "Bachelor of Arts in American Studies", "American Studies", "bachelors", 48,
       "American Studies Program", "05.01",
       "Interdisciplinary examination of United States culture, society, and identity through history, literature, media, and the arts.",
       "Students who want to understand America across disciplines — culture, race, politics, and the arts — rather than through a single department."),
    _p("tufts-anthropology-ba", _AS, "Bachelor of Arts in Anthropology", "Anthropology", "bachelors", 48,
       "Department of Anthropology", "45.02",
       "The comparative study of human societies, cultures, language, and biology across time, from ethnographic fieldwork to archaeology.",
       "Students curious about human diversity and cultural difference who want fieldwork-based training for careers in research, public health, law, or global work."),
    _p("tufts-archaeology-ba", _AS, "Bachelor of Arts in Archaeology", "Archaeology", "bachelors", 48,
       "Archaeology Program", "45.03",
       "The recovery and interpretation of the human past through material remains, spanning excavation methods, ancient societies, and heritage science.",
       "Students fascinated by ancient civilizations and the material record who want hands-on training in excavation, analysis, and interpretation."),
    _p("tufts-architectural-studies-ba", _AS, "Bachelor of Arts in Architectural Studies", "Architectural Studies", "bachelors", 48,
       "Department of the History of Art and Architecture", "04.02",
       "The study of the built environment — architectural history, theory, and design thinking — as a liberal-arts foundation for design and the humanities.",
       "Students interested in buildings, cities, and design who want a liberal-arts path toward architecture, planning, or graduate design study."),
    _p("tufts-art-history-ba", _AS, "Bachelor of Arts in Art History", "Art History", "bachelors", 48,
       "Department of the History of Art and Architecture", "50.07",
       "The history and interpretation of art and visual culture from antiquity to the present, with access to Boston's museums and the Tufts Art Galleries.",
       "Students who want to read images and objects closely for careers in museums, galleries, conservation, or graduate study in the history of art."),
    _p("tufts-biochemistry-bs", _AS, "Bachelor of Science in Biochemistry", "Biochemistry", "bachelors", 48,
       "Department of Chemistry", "26.02",
       "The chemistry of living systems — proteins, enzymes, and metabolism — at the interface of molecular biology and organic and physical chemistry.",
       "Pre-medical and research-bound students who want a rigorous molecular-science major bridging chemistry and biology."),
    _p("tufts-biology-bs", _AS, "Bachelor of Science in Biology", "Biology", "bachelors", 48,
       "Department of Biology", "26.01",
       "From molecular and cellular biology through genetics, physiology, and ecology, with extensive laboratory and independent-research opportunities.",
       "Students preparing for medicine, biomedical research, or graduate study who want a broad, lab-intensive foundation in the life sciences."),
    _p("tufts-biopsychology-bs", _AS, "Bachelor of Science in Biopsychology", "Biopsychology", "bachelors", 48,
       "Department of Psychology", "30.10",
       "The biological bases of behavior — how the brain, hormones, and nervous system shape perception, emotion, and action.",
       "Students who want to study behavior through the lens of biology, with an eye toward neuroscience, medicine, or research."),
    _p("tufts-chemistry-bs", _AS, "Bachelor of Science in Chemistry", "Chemistry", "bachelors", 48,
       "Department of Chemistry", "40.05",
       "Organic, inorganic, physical, and analytical chemistry with a strong undergraduate research culture in synthesis and materials.",
       "Students who want to understand and create molecules and pursue chemistry, medicine, or materials science."),
    _p("tufts-classical-studies-ba", _AS, "Bachelor of Arts in Classical Studies", "Classical Studies", "bachelors", 48,
       "Department of Classical Studies", "16.12",
       "The languages, literature, history, and archaeology of ancient Greece and Rome, from Homer and Virgil to Roman law and material culture.",
       "Students who love the ancient world and want to read its languages and study the classical foundations of Western thought."),
    _p("tufts-cognitive-brain-sciences-bs", _AS, "Bachelor of Science in Cognitive and Brain Sciences", "Cognitive and Brain Sciences", "bachelors", 48,
       "Department of Psychology", "30.25",
       "How minds and brains represent, learn, and reason — integrating psychology, neuroscience, linguistics, philosophy, and computation.",
       "Students fascinated by how the mind works who want an interdisciplinary path toward neuroscience, AI, or cognitive research."),
    _p("tufts-community-health-ba", _AS, "Bachelor of Arts in Community Health", "Community Health", "bachelors", 48,
       "Department of Community Health", "51.22",
       "The social, behavioral, and environmental determinants of health and the design of programs and policies that improve population well-being.",
       "Students committed to public health and health equity who want a population-level foundation for careers in health, policy, or medicine."),
    _p("tufts-computer-science-bs", _AS, "Bachelor of Science in Computer Science", "Computer Science", "bachelors", 48,
       "Department of Computer Science", "11.07",
       "Algorithms, systems, theory, and applications from machine learning to human-computer interaction, offered jointly across Arts and Sciences and Engineering.",
       "Students who want to build software and reason about computation, whether headed to industry or graduate research."),
    _p("tufts-economics-ba", _AS, "Bachelor of Arts in Economics", "Economics", "bachelors", 48,
       "Department of Economics", "45.06",
       "Micro- and macroeconomic theory with empirical and econometric training, and applications from public policy to finance.",
       "Students who want analytical tools for careers in finance, consulting, policy, or economics graduate study."),
    _p("tufts-quantitative-economics-bs", _AS, "Bachelor of Science in Quantitative Economics", "Quantitative Economics", "bachelors", 48,
       "Department of Economics", "45.06",
       "A mathematically intensive economics major emphasizing statistics, econometrics, and formal modeling for data-driven economic analysis.",
       "Students who want a quantitative, math-heavy economics degree for careers in data-driven finance, analytics, or economics research."),
    _p("tufts-education-ba", _AS, "Bachelor of Arts in Education", "Education", "bachelors", 48,
       "Department of Education", "13.01",
       "The study of learning, teaching, and schooling across social, cognitive, and policy dimensions, with pathways toward teacher licensure.",
       "Students who want to understand how people learn and to prepare for careers in teaching, education policy, or research."),
    _p("tufts-english-ba", _AS, "Bachelor of Arts in English", "English", "bachelors", 48,
       "Department of English", "23.01",
       "The close reading and interpretation of literature in English alongside creative and expository writing across periods and genres.",
       "Students who love reading and writing and want strong analytical and communication skills for careers in law, media, publishing, or the academy."),
    _p("tufts-environmental-studies-ba", _AS, "Bachelor of Arts in Environmental Studies", "Environmental Studies", "bachelors", 48,
       "Environmental Studies Program", "03.01",
       "An interdisciplinary examination of environmental challenges through the natural sciences, social sciences, and policy.",
       "Students committed to the environment who want to combine science, policy, and ethics to address climate and sustainability challenges."),
    _p("tufts-film-media-studies-ba", _AS, "Bachelor of Arts in Film and Media Studies", "Film and Media Studies", "bachelors", 48,
       "Film and Media Studies Program", "50.06",
       "The history, theory, and practice of film and media, from analysis of moving images to production and screen culture.",
       "Students who want to analyze and create film and media for careers in production, criticism, or media industries."),
    _p("tufts-french-ba", _AS, "Bachelor of Arts in French", "French", "bachelors", 48,
       "Department of Romance Studies", "16.09",
       "French language, literature, and the cultures of France and the Francophone world, from medieval texts to contemporary film.",
       "Students who want fluency in French and deep engagement with Francophone literature and culture for global and humanities careers."),
    _p("tufts-german-studies-ba", _AS, "Bachelor of Arts in German Language and Cultural Studies", "German", "bachelors", 48,
       "Department of International Literary and Cultural Studies", "16.05",
       "German language together with the literature, philosophy, film, and history of the German-speaking world.",
       "Students who want fluency in German and engagement with its literary and intellectual traditions."),
    _p("tufts-history-ba", _AS, "Bachelor of Arts in History", "History", "bachelors", 48,
       "Department of History", "54.01",
       "The critical study of the human past across regions and eras, emphasizing primary-source research and historical argument.",
       "Students who want to investigate the past and build research and writing skills for law, policy, education, or the academy."),
    _p("tufts-intl-literary-cultural-ba", _AS, "Bachelor of Arts in International Literary and Cultural Studies", "International Literary and Cultural Studies", "bachelors", 48,
       "Department of International Literary and Cultural Studies", "16.01",
       "Comparative study of world literatures and cultures across languages, with training in translation and cross-cultural interpretation.",
       "Students drawn to languages and world literatures who want a comparative, multilingual humanities major."),
    _p("tufts-international-relations-ba", _AS, "Bachelor of Arts in International Relations", "International Relations", "bachelors", 48,
       "International Relations Program", "45.09",
       "An interdisciplinary major on global politics, economics, security, and culture, drawing on Tufts' strength in international affairs.",
       "Students aiming for careers in diplomacy, global development, international business, or security who want a broad global-affairs foundation."),
    _p("tufts-italian-studies-ba", _AS, "Bachelor of Arts in Italian Studies", "Italian Studies", "bachelors", 48,
       "Department of Romance Studies", "16.09",
       "Italian language and the literature, art, and history of Italy from the Renaissance to the present.",
       "Students who want fluency in Italian and engagement with Italy's literary and cultural heritage."),
    _p("tufts-judaic-studies-ba", _AS, "Bachelor of Arts in Judaic Studies", "Judaic Studies", "bachelors", 48,
       "Judaic Studies Program", "38.02",
       "The interdisciplinary study of Jewish history, religion, languages, literature, and culture across the ancient and modern worlds.",
       "Students interested in Jewish history, thought, and culture who want an interdisciplinary humanities major."),
    _p("tufts-latin-american-studies-ba", _AS, "Bachelor of Arts in Latin American Studies", "Latin American Studies", "bachelors", 48,
       "Latin American Studies Program", "05.01",
       "Interdisciplinary study of the history, politics, cultures, and languages of Latin America and its diasporas.",
       "Students focused on Latin America who want to combine language, history, and social science for regional expertise."),
    _p("tufts-mathematics-bs", _AS, "Bachelor of Science in Mathematics", "Mathematics", "bachelors", 48,
       "Department of Mathematics", "27.01",
       "Pure and applied mathematics from analysis and algebra to probability and modeling, with a strong proof-based core.",
       "Students who love rigorous reasoning and want a mathematics foundation for research, data science, finance, or teaching."),
    _p("tufts-applied-mathematics-bs", _AS, "Bachelor of Science in Applied Mathematics", "Applied Mathematics", "bachelors", 48,
       "Department of Mathematics", "27.03",
       "Mathematics oriented toward real-world problems — modeling, differential equations, numerical methods, and applications across science and engineering.",
       "Students who want to use advanced mathematics to model and solve problems in science, engineering, and data-driven fields."),
    _p("tufts-middle-eastern-studies-ba", _AS, "Bachelor of Arts in Middle Eastern Studies", "Middle Eastern Studies", "bachelors", 48,
       "Middle Eastern Studies Program", "05.01",
       "Interdisciplinary study of the languages, history, religions, and politics of the Middle East and North Africa.",
       "Students focused on the Middle East who want language training and regional expertise for global-affairs, policy, or research careers."),
    _p("tufts-music-ba", _AS, "Bachelor of Arts in Music, Sound and Culture", "Music, Sound and Culture", "bachelors", 48,
       "Department of Music", "50.09",
       "The study of music and sound across history, theory, composition, ethnomusicology, and performance in cultural context.",
       "Students who want to study music broadly — as culture, sound, and practice — rather than through performance alone."),
    _p("tufts-philosophy-ba", _AS, "Bachelor of Arts in Philosophy", "Philosophy", "bachelors", 48,
       "Department of Philosophy", "38.01",
       "Rigorous inquiry into questions of knowledge, ethics, mind, and reality through close reasoning and argument.",
       "Students who want to sharpen reasoning and confront fundamental questions, whether for law, policy, or graduate study."),
    _p("tufts-physics-bs", _AS, "Bachelor of Science in Physics", "Physics", "bachelors", 48,
       "Department of Physics and Astronomy", "40.08",
       "The fundamental laws governing matter and energy, from mechanics and electromagnetism to quantum physics, with laboratory and research training.",
       "Students who want to understand nature at its most fundamental level and prepare for physics, engineering, or research.",
       tracks=["Applied Physics", "Chemical Physics"]),
    _p("tufts-astrophysics-bs", _AS, "Bachelor of Science in Astrophysics", "Astrophysics", "bachelors", 48,
       "Department of Physics and Astronomy", "40.02",
       "The physics of stars, galaxies, and the cosmos, combining astronomy with the tools of theoretical and observational physics.",
       "Students captivated by the universe who want to combine physics and astronomy toward research in astrophysics."),
    _p("tufts-political-science-ba", _AS, "Bachelor of Arts in Political Science", "Political Science", "bachelors", 48,
       "Department of Political Science", "45.10",
       "The study of government, political behavior, and public policy across American, comparative, and international politics and political theory.",
       "Students interested in government, law, and public affairs who want analytical training for policy, law, or civic careers."),
    _p("tufts-psychology-bs", _AS, "Bachelor of Science in Psychology", "Psychology", "bachelors", 48,
       "Department of Psychology", "42.01",
       "The scientific study of mind and behavior across cognitive, developmental, social, and clinical perspectives, grounded in empirical methods.",
       "Students interested in why people think and behave as they do who want research-based training for psychology, health, or human-services careers.",
       tracks=["Clinical Psychology", "Human Factors"]),
    _p("tufts-race-colonialism-diaspora-ba", _AS, "Bachelor of Arts in Race, Colonialism and Diaspora Studies", "Race, Colonialism and Diaspora Studies", "bachelors", 48,
       "Department of Studies in Race, Colonialism, and Diaspora", "05.02",
       "Interdisciplinary analysis of race, colonialism, migration, and diaspora across global histories and cultures.",
       "Students who want to study structures of race and empire critically across the humanities and social sciences."),
    _p("tufts-religion-ba", _AS, "Bachelor of Arts in Religion", "Religion", "bachelors", 48,
       "Department of Religion", "38.02",
       "The comparative and critical study of religious traditions, texts, and practices across cultures and history.",
       "Students curious about religion's role in human life who want an interdisciplinary humanities approach to belief and culture."),
    _p("tufts-russian-east-european-ba", _AS, "Bachelor of Arts in Russian and East European Studies", "Russian and East European Studies", "bachelors", 48,
       "Russian and East European Studies Program", "16.04",
       "The languages, literature, history, and politics of Russia and Eastern Europe, combining language study with regional expertise.",
       "Students focused on Russia and Eastern Europe who want language skills and regional knowledge for global-affairs or research careers."),
    _p("tufts-science-technology-society-ba", _AS, "Bachelor of Arts in Science, Technology and Society", "Science, Technology and Society", "bachelors", 48,
       "Science, Technology, and Society Program", "30.15",
       "How science and technology shape — and are shaped by — society, ethics, and policy, bridging the sciences and the humanities.",
       "Students who want to examine the social and ethical dimensions of science and technology across disciplines."),
    _p("tufts-sociology-ba", _AS, "Bachelor of Arts in Sociology", "Sociology", "bachelors", 48,
       "Department of Sociology", "45.11",
       "The study of social structures, institutions, and inequality, from families and organizations to race, class, and globalization.",
       "Students who want to analyze how societies and institutions work and to address inequality through research or policy."),
    _p("tufts-spanish-ba", _AS, "Bachelor of Arts in Spanish", "Spanish", "bachelors", 48,
       "Department of Romance Studies", "16.09",
       "Spanish language and the literatures and cultures of Spain and Latin America, from classic texts to contemporary media.",
       "Students who want fluency in Spanish and engagement with the Hispanic world's literary and cultural traditions."),
    _p("tufts-theatre-dance-performance-ba", _AS, "Bachelor of Arts in Theatre, Dance and Performance Studies", "Theatre, Dance and Performance Studies", "bachelors", 48,
       "Department of Theatre, Dance, and Performance Studies", "50.05",
       "The study and practice of theatre, dance, and performance across history, theory, and studio work.",
       "Students who want to study and make performance — on stage and as a lens on culture — across theatre and dance."),
    _p("tufts-wgss-ba", _AS, "Bachelor of Arts in Women's, Gender, and Sexuality Studies", "Women's, Gender, and Sexuality Studies", "bachelors", 48,
       "Women's, Gender, and Sexuality Studies Program", "05.02",
       "Interdisciplinary analysis of gender and sexuality across culture, politics, history, and science.",
       "Students who want to study gender and sexuality critically across the humanities and social sciences."),
    _p("tufts-child-study-human-development-ba", _AS, "Bachelor of Arts in Child Study and Human Development", "Child Study and Human Development", "bachelors", 48,
       "Eliot-Pearson Department of Child Study and Human Development", "19.07",
       "The study of human development from childhood through adolescence, integrating psychology, education, and social policy.",
       "Students committed to children, families, and human development who want a foundation for education, counseling, or child-focused careers."),
    _p("tufts-geological-sciences-bs", _AS, "Bachelor of Science in Geological Sciences", "Geological Sciences", "bachelors", 48,
       "Department of Earth and Climate Sciences", "40.06",
       "The processes shaping the Earth — from plate tectonics and minerals to surface systems and the geologic record of climate.",
       "Students fascinated by the Earth who want field- and lab-based training toward geoscience, environmental, or climate careers."),

    # ══ School of Engineering — undergraduate ══
    _p("tufts-biomedical-engineering-bs", _ENG, "Bachelor of Science in Biomedical Engineering", "Biomedical Engineering", "bachelors", 48,
       "Department of Biomedical Engineering", "14.05",
       "Engineering applied to medicine and biology — biomaterials, imaging, biomechanics, and devices that improve human health.",
       "Students who want to apply engineering to medicine and the life sciences, headed toward biotech, medical devices, or medicine."),
    _p("tufts-chemical-engineering-bs", _ENG, "Bachelor of Science in Chemical Engineering", "Chemical Engineering", "bachelors", 48,
       "Department of Chemical and Biological Engineering", "14.07",
       "The design of processes that transform matter and energy — reactions, separations, and transport — across energy, materials, and biotechnology.",
       "Students who like chemistry and problem-solving at scale, aiming for careers in energy, materials, pharmaceuticals, or biotech."),
    _p("tufts-civil-engineering-bs", _ENG, "Bachelor of Science in Civil Engineering", "Civil Engineering", "bachelors", 48,
       "Department of Civil and Environmental Engineering", "14.08",
       "The design and analysis of infrastructure — structures, transportation, and geotechnical and water systems — for resilient communities.",
       "Students who want to design the built environment and infrastructure that communities depend on."),
    _p("tufts-environmental-engineering-bs", _ENG, "Bachelor of Science in Environmental Engineering", "Environmental Engineering", "bachelors", 48,
       "Department of Civil and Environmental Engineering", "14.14",
       "Engineering for clean water, air, and land — treatment systems, environmental modeling, and sustainable resource management.",
       "Students who want to use engineering to protect the environment and public health through water, air, and sustainability work."),
    _p("tufts-computer-engineering-bs", _ENG, "Bachelor of Science in Computer Engineering", "Computer Engineering", "bachelors", 48,
       "Department of Electrical and Computer Engineering", "14.09",
       "The design of computing hardware and embedded systems, spanning digital logic, architecture, and the hardware-software interface.",
       "Students who want to build the hardware and embedded systems behind modern computing, from chips to devices."),
    _p("tufts-electrical-engineering-bs", _ENG, "Bachelor of Science in Electrical Engineering", "Electrical Engineering", "bachelors", 48,
       "Department of Electrical and Computer Engineering", "14.10",
       "The science and design of electrical and electronic systems — circuits, signals, power, and communications.",
       "Students fascinated by electronics, signals, and power who want to design the systems behind modern technology."),
    _p("tufts-data-science-bs", _ENG, "Bachelor of Science in Data Science", "Data Science", "bachelors", 48,
       "Department of Computer Science", "30.70",
       "The computational and statistical foundations of extracting insight from data — machine learning, data management, and modeling.",
       "Students who want to combine computing and statistics to turn data into insight across science, business, and society."),
    _p("tufts-engineering-physics-bs", _ENG, "Bachelor of Science in Engineering Physics", "Engineering Physics", "bachelors", 48,
       "School of Engineering", "14.12",
       "A rigorous blend of physics and engineering for students who want deep physical foundations applied to technology and research.",
       "Students who want the analytical depth of physics combined with the applied problem-solving of engineering."),
    _p("tufts-mechanical-engineering-bs", _ENG, "Bachelor of Science in Mechanical Engineering", "Mechanical Engineering", "bachelors", 48,
       "Department of Mechanical Engineering", "14.19",
       "The design and analysis of machines, mechanisms, and energy systems — from mechanics and materials to robotics and thermofluids.",
       "Students who like to design and build physical systems, from robots and vehicles to energy and manufacturing technology."),
    _p("tufts-human-factors-engineering-bs", _ENG, "Bachelor of Science in Human Factors Engineering", "Human Factors Engineering", "bachelors", 48,
       "Department of Mechanical Engineering", "14.19",
       "The engineering of systems, products, and interfaces around human capabilities, blending mechanical design with cognitive science.",
       "Students who want to design technology around people — usability, ergonomics, and human-centered systems."),

    # ══ SMFA — undergraduate ══
    _p("tufts-bfa", _SMFA, "Bachelor of Fine Arts", "Studio Art", "bachelors", 48,
       "School of the Museum of Fine Arts at Tufts", "50.07",
       "An interdisciplinary, self-directed studio-art degree spanning painting, sculpture, photography, printmaking, new media, and performance.",
       "Artists who want an open, cross-media studio education with the resources of a research university behind it."),
]

# ── Graduate School of Arts and Sciences (GSAS) — master's / doctoral ──
PROGRAMS += [
    _p("tufts-art-history-museum-ma", _AS, "Master of Arts in Art History and Museum Studies", "Art History and Museum Studies", "masters", 24,
       "Department of the History of Art and Architecture", "50.07",
       "Graduate study of art history paired with museum theory and practice, preparing students for curatorial and museum careers.",
       "Graduates aiming for museum, curatorial, or gallery careers who want art-historical depth with hands-on museum training.", credits=30),
    _p("tufts-classics-ma", _AS, "Master of Arts in Classics", "Classics", "masters", 24,
       "Department of Classical Studies", "16.12",
       "Advanced study of Greek and Latin languages, literature, and ancient history for scholarly and teaching preparation.",
       "Students deepening their classical languages and preparing for doctoral study or teaching in the ancient world.", credits=30),
    _p("tufts-english-phd", _AS, "Doctor of Philosophy in English", "English", "phd", 60,
       "Department of English", "23.01",
       "Doctoral research in literature in English, with training in critical theory, historical fields, and college teaching.",
       "Scholars committed to original literary research and a career in university teaching and scholarship."),
    _p("tufts-history-ma", _AS, "Master of Arts in History", "History", "masters", 24,
       "Department of History", "54.01",
       "Graduate training in historical research, methods, and writing across fields and regions.",
       "Students strengthening historical research skills for doctoral study, teaching, or public-history careers.", credits=30),
    _p("tufts-history-phd", _AS, "Doctor of Philosophy in History", "History", "phd", 60,
       "Department of History", "54.01",
       "Doctoral research in history, emphasizing archival scholarship, historiography, and the training of historians.",
       "Scholars pursuing original historical research and a career in academic or public history."),
    _p("tufts-music-ma", _AS, "Master of Arts in Music", "Music", "masters", 24,
       "Department of Music", "50.09",
       "Graduate study in musicology, ethnomusicology, theory, and composition within a research-university setting.",
       "Musicians and scholars deepening their study of music toward doctoral work, teaching, or professional practice.", credits=30),
    _p("tufts-philosophy-ma", _AS, "Master of Arts in Philosophy", "Philosophy", "masters", 24,
       "Department of Philosophy", "38.01",
       "Advanced training in philosophical analysis and argument across metaphysics, epistemology, ethics, and the history of philosophy.",
       "Students strengthening their philosophical foundations before doctoral study or professional work requiring rigorous reasoning.", credits=30),
    _p("tufts-drama-phd", _AS, "Doctor of Philosophy in Theatre and Performance Studies", "Theatre and Performance Studies", "phd", 60,
       "Department of Theatre, Dance, and Performance Studies", "50.05",
       "Doctoral research in drama, theatre history, and performance studies, integrating scholarship with theatrical practice.",
       "Scholars and theatre artists pursuing original research and a career in performance studies and university teaching."),
    _p("tufts-economics-ma", _AS, "Master of Arts in Economics", "Economics", "masters", 24,
       "Department of Economics", "45.06",
       "Graduate training in economic theory and applied econometrics for careers in research, policy, and industry.",
       "Students strengthening quantitative economics skills for doctoral study or applied research and policy roles.", credits=30),
    _p("tufts-economics-phd", _AS, "Doctor of Philosophy in Economics", "Economics", "phd", 60,
       "Department of Economics", "45.06",
       "Doctoral research in economics across micro, macro, and applied fields, with strong econometric and theoretical training.",
       "Scholars pursuing original economic research and a career in academia, government, or research institutions."),
    _p("tufts-uep-ma", _AS, "Master of Arts in Urban and Environmental Policy and Planning", "Urban and Environmental Policy and Planning", "masters", 24,
       "Department of Urban and Environmental Policy and Planning", "04.03",
       "Graduate training in equitable planning and policy across housing, community development, transportation, and the environment.",
       "Aspiring planners and policy practitioners who want to advance social and environmental justice in cities and communities.", credits=42),
    _p("tufts-environmental-policy-ms", _AS, "Master of Science in Environmental Policy and Planning", "Environmental Policy and Planning", "masters", 24,
       "Department of Urban and Environmental Policy and Planning", "03.02",
       "Graduate study of environmental policy, planning, and management, integrating science, policy, and community practice.",
       "Practitioners focused on the environment who want policy and planning tools for sustainability and climate careers.", credits=42),
    _p("tufts-public-policy-mpp", _AS, "Master of Public Policy", "Public Policy", "masters", 24,
       "Department of Urban and Environmental Policy and Planning", "44.05",
       "Professional training in policy analysis, program evaluation, and public management for effective, equitable governance.",
       "Students headed for policy-analysis and public-management careers in government, nonprofits, and advocacy.", credits=42),
    _p("tufts-cshd-ma", _AS, "Master of Arts in Child Study and Human Development", "Child Study and Human Development", "masters", 24,
       "Eliot-Pearson Department of Child Study and Human Development", "19.07",
       "Graduate study of child and adolescent development across research, education, and applied practice.",
       "Practitioners and researchers focused on children and families who want developmental science for education, policy, or clinical paths.", credits=30),
    _p("tufts-cshd-phd", _AS, "Doctor of Philosophy in Child Study and Human Development", "Child Study and Human Development", "phd", 60,
       "Eliot-Pearson Department of Child Study and Human Development", "19.07",
       "Doctoral research on human development from infancy through adolescence, spanning cognition, emotion, and social context.",
       "Scholars pursuing original developmental research and careers in academia, policy, or applied child-development science."),
    _p("tufts-psychology-phd", _AS, "Doctor of Philosophy in Psychology", "Psychology", "phd", 60,
       "Department of Psychology", "42.27",
       "Doctoral research in psychology across biological, cognitive, developmental, social, and clinical-science concentrations.",
       "Scholars pursuing original psychological research and a career in academic or applied research science."),
    _p("tufts-biology-ms", _AS, "Master of Science in Biology", "Biology", "masters", 24,
       "Department of Biology", "26.01",
       "Graduate study in the life sciences across molecular, cellular, organismal, and ecological biology.",
       "Students deepening their biology training for doctoral study, health professions, or research and industry roles.", credits=30),
    _p("tufts-biology-phd", _AS, "Doctor of Philosophy in Biology", "Biology", "phd", 60,
       "Department of Biology", "26.01",
       "Doctoral research spanning molecular and cellular biology, genetics, ecology, and evolution.",
       "Scholars pursuing original life-science research and a career in academic or industry biology."),
    _p("tufts-chemistry-ms", _AS, "Master of Science in Chemistry", "Chemistry", "masters", 24,
       "Department of Chemistry", "40.05",
       "Graduate study across organic, inorganic, physical, and biological chemistry with laboratory research.",
       "Students deepening their chemistry training toward doctoral study or research and industry careers.", credits=30),
    _p("tufts-chemistry-phd", _AS, "Doctor of Philosophy in Chemistry", "Chemistry", "phd", 60,
       "Department of Chemistry", "40.05",
       "Doctoral research across the chemical sciences, from synthesis and catalysis to physical and biological chemistry.",
       "Scholars pursuing original chemical research and a career in academia or the chemical and pharmaceutical industries.",
       tracks=["Chemical Physics", "Biotechnology"]),
    _p("tufts-biotechnology-ms", _AS, "Master of Science in Biotechnology", "Biotechnology", "masters", 24,
       "Department of Chemistry", "26.12",
       "Applied graduate training at the interface of chemistry, molecular biology, and industry, oriented toward the biotech sector.",
       "Students aiming for careers in the biotechnology and pharmaceutical industries who want applied lab and science training.", credits=30),
    _p("tufts-physics-ms", _AS, "Master of Science in Physics", "Physics", "masters", 24,
       "Department of Physics and Astronomy", "40.08",
       "Graduate study of physics across theoretical and experimental fields, including astrophysics and chemical physics.",
       "Students deepening their physics training toward doctoral study or technical and research careers.", credits=30),
    _p("tufts-physics-phd", _AS, "Doctor of Philosophy in Physics", "Physics", "phd", 60,
       "Department of Physics and Astronomy", "40.08",
       "Doctoral research across physics and astrophysics, from cosmology and particle physics to condensed matter and biophysics.",
       "Scholars pursuing original physics research and a career in academic, national-lab, or industry research.",
       tracks=["Astrophysics", "Chemical Physics", "Physics Education"]),
    _p("tufts-mathematics-ms", _AS, "Master of Science in Mathematics", "Mathematics", "masters", 24,
       "Department of Mathematics", "27.01",
       "Graduate study in pure and applied mathematics, from analysis and algebra to computational and applied fields.",
       "Students deepening their mathematics for doctoral study, teaching, or quantitative careers.", credits=30),
    _p("tufts-mathematics-phd", _AS, "Doctor of Philosophy in Mathematics", "Mathematics", "phd", 60,
       "Department of Mathematics", "27.01",
       "Doctoral research in mathematics across pure and applied fields, culminating in an original dissertation.",
       "Scholars pursuing original mathematical research and a career in academic or research mathematics."),
    _p("tufts-data-analytics-ms", _AS, "Master of Science in Data Analytics", "Data Analytics", "masters", 24,
       "Data Analytics Program", "30.71",
       "An interdisciplinary professional master's building applied skills in statistics, machine learning, and data-driven decision making.",
       "Working professionals and graduates who want applied analytics skills to move into data-focused roles across industries.", credits=30),
    _p("tufts-leadership-ma", _AS, "Master of Arts in Leadership", "Leadership", "masters", 24,
       "Leadership Program", "52.02",
       "An online professional master's developing leadership, organizational, and change-management capabilities for the public and private sectors.",
       "Working professionals seeking to strengthen leadership and management skills through a flexible online graduate program.",
       delivery_format="online", credits=30),

    # ══ School of Engineering — graduate ══
    _p("tufts-computer-science-ms", _ENG, "Master of Science in Computer Science", "Computer Science", "masters", 24,
       "Department of Computer Science", "11.07",
       "Advanced graduate study across algorithms, systems, machine learning, and human-computer interaction.",
       "Graduates and professionals deepening their computer-science expertise for advanced technical or research roles.", credits=30),
    _p("tufts-computer-science-phd", _ENG, "Doctor of Philosophy in Computer Science", "Computer Science", "phd", 60,
       "Department of Computer Science", "11.07",
       "Doctoral research in computer science, from theory and systems to machine learning and human-robot interaction.",
       "Scholars pursuing original computing research and a career in academic or industrial research."),
    _p("tufts-data-science-ms", _ENG, "Master of Science in Data Science", "Data Science", "masters", 24,
       "Department of Computer Science", "30.70",
       "A professional master's uniting computer science and statistics for scalable data analysis and machine learning.",
       "Graduates and professionals building rigorous data-science skills for engineering and analytics careers.", credits=30),
    _p("tufts-artificial-intelligence-ms", _ENG, "Master of Science in Artificial Intelligence", "Artificial Intelligence", "masters", 24,
       "Department of Computer Science", "11.01",
       "Focused graduate study of the methods behind modern AI — machine learning, reasoning, perception, and their applications.",
       "Students and professionals who want deep, applied training in artificial intelligence and machine learning.", credits=30),
    _p("tufts-human-robot-interaction-ms", _ENG, "Master of Science in Human-Robot Interaction", "Human-Robot Interaction", "masters", 24,
       "Department of Computer Science", "11.07",
       "An interdisciplinary master's on how people and robots interact, spanning robotics, cognitive science, and interface design.",
       "Students drawn to robotics and cognitive science who want to design how humans and robots work together.", credits=30),
    _p("tufts-mechanical-engineering-ms", _ENG, "Master of Science in Mechanical Engineering", "Mechanical Engineering", "masters", 24,
       "Department of Mechanical Engineering", "14.19",
       "Advanced graduate study across mechanics, dynamics, controls, thermofluids, and robotics.",
       "Engineers deepening their mechanical-engineering expertise for advanced design, research, or R&D roles.", credits=30),
    _p("tufts-mechanical-engineering-phd", _ENG, "Doctor of Philosophy in Mechanical Engineering", "Mechanical Engineering", "phd", 60,
       "Department of Mechanical Engineering", "14.19",
       "Doctoral research in mechanical engineering, from robotics and soft materials to biomechanics and energy systems.",
       "Scholars pursuing original mechanical-engineering research and a career in academia or advanced industry R&D."),
    _p("tufts-electrical-engineering-ms", _ENG, "Master of Science in Electrical Engineering", "Electrical Engineering", "masters", 24,
       "Department of Electrical and Computer Engineering", "14.10",
       "Advanced graduate study in circuits, signals, communications, and electronic and photonic systems.",
       "Engineers deepening their electrical-engineering expertise for advanced technical and research careers.", credits=30),
    _p("tufts-ece-phd", _ENG, "Doctor of Philosophy in Electrical and Computer Engineering", "Electrical and Computer Engineering", "phd", 60,
       "Department of Electrical and Computer Engineering", "14.10",
       "Doctoral research spanning signals and systems, hardware, communications, and embedded and cyber-physical systems.",
       "Scholars pursuing original electrical and computer engineering research and a career in academia or industry R&D."),
    _p("tufts-computer-engineering-ms", _ENG, "Master of Science in Computer Engineering", "Computer Engineering", "masters", 24,
       "Department of Electrical and Computer Engineering", "14.09",
       "Advanced graduate study of computing hardware, architecture, and embedded and cyber-physical systems.",
       "Engineers deepening their expertise in computing hardware and embedded systems for advanced roles.", credits=30),
    _p("tufts-biomedical-engineering-ms", _ENG, "Master of Science in Biomedical Engineering", "Biomedical Engineering", "masters", 24,
       "Department of Biomedical Engineering", "14.05",
       "Advanced graduate study at the interface of engineering and medicine — biomaterials, imaging, and biomedical devices.",
       "Engineers and scientists deepening biomedical-engineering expertise for biotech, devices, or research careers.", credits=30),
    _p("tufts-biomedical-engineering-phd", _ENG, "Doctor of Philosophy in Biomedical Engineering", "Biomedical Engineering", "phd", 60,
       "Department of Biomedical Engineering", "14.05",
       "Doctoral research applying engineering to biology and medicine, from tissue engineering and biomaterials to neural engineering.",
       "Scholars pursuing original biomedical-engineering research and a career in academia or the medical-technology industry."),
    _p("tufts-chemical-engineering-ms", _ENG, "Master of Science in Chemical Engineering", "Chemical Engineering", "masters", 24,
       "Department of Chemical and Biological Engineering", "14.07",
       "Advanced graduate study of chemical and biological process engineering, from reaction and transport to biotechnology.",
       "Engineers deepening chemical-engineering expertise for advanced roles in energy, materials, and biotech.", credits=30),
    _p("tufts-chemical-engineering-phd", _ENG, "Doctor of Philosophy in Chemical Engineering", "Chemical Engineering", "phd", 60,
       "Department of Chemical and Biological Engineering", "14.07",
       "Doctoral research in chemical and biological engineering, from catalysis and materials to biomolecular engineering.",
       "Scholars pursuing original chemical-engineering research and a career in academia or advanced industry R&D."),
    _p("tufts-civil-environmental-ms", _ENG, "Master of Science in Civil and Environmental Engineering", "Civil and Environmental Engineering", "masters", 24,
       "Department of Civil and Environmental Engineering", "14.08",
       "Advanced graduate study across structures, geotechnics, water resources, and environmental engineering.",
       "Engineers deepening civil and environmental expertise for advanced practice, design, or research.", credits=30),
    _p("tufts-civil-environmental-phd", _ENG, "Doctor of Philosophy in Civil and Environmental Engineering", "Civil and Environmental Engineering", "phd", 60,
       "Department of Civil and Environmental Engineering", "14.08",
       "Doctoral research in civil and environmental engineering, from resilient infrastructure to water and environmental systems.",
       "Scholars pursuing original civil and environmental research and a career in academia or advanced practice."),
    _p("tufts-materials-science-ms", _ENG, "Master of Science in Materials Science and Engineering", "Materials Science and Engineering", "masters", 24,
       "School of Engineering", "14.18",
       "Interdepartmental graduate study of the structure, properties, and processing of materials across engineering fields.",
       "Engineers and scientists focused on materials who want cross-disciplinary graduate training for R&D careers.", credits=30),
    _p("tufts-human-factors-ms", _ENG, "Master of Science in Human Factors Engineering", "Human Factors Engineering", "masters", 24,
       "Department of Mechanical Engineering", "14.19",
       "Graduate study of human-centered design, usability, and cognitive ergonomics for people-centered engineering.",
       "Professionals designing usable, human-centered systems who want rigorous human-factors and UX foundations.", credits=30),
    # NOTE: the joint M.S. in Cybersecurity and Public Policy is a single Fletcher/Engineering
    # degree; it is carried once under The Fletcher School (tufts-fletcher-mscpp), not duplicated here.
    _p("tufts-engineering-management-ms", _ENG, "Master of Science in Engineering Management", "Engineering Management", "masters", 24,
       "Gordon Institute", "15.15",
       "A professional master's combining engineering with management, finance, and leadership for technical organizations.",
       "Engineers moving into technical leadership who want management, finance, and strategy skills alongside their technical base.",
       delivery_format="online", credits=30),
    _p("tufts-innovation-management-ms", _ENG, "Master of Science in Innovation and Management", "Innovation and Management", "masters", 12,
       "Gordon Institute", "52.02",
       "An intensive professional master's in technology innovation, entrepreneurship, and management for engineers and scientists.",
       "Technically-trained graduates who want entrepreneurship and management skills to lead innovation and new ventures.", credits=30),

    # ══ Occupational Therapy (Arts & Sciences) ══
    _p("tufts-occupational-therapy-otd", _AS, "Doctor of Occupational Therapy", "Occupational Therapy", "professional", 36,
       "Department of Occupational Therapy", "51.23",
       "The entry-level clinical doctorate preparing occupational therapists to help people participate in the activities that matter to them.",
       "Students entering the occupational-therapy profession who want a clinical doctorate leading to licensure and practice."),
    _p("tufts-occupational-therapy-ms", _AS, "Master of Science in Occupational Therapy", "Occupational Therapy", "masters", 24,
       "Department of Occupational Therapy", "51.23",
       "Post-professional graduate study for practicing occupational therapists advancing clinical expertise and scholarship.",
       "Practicing occupational therapists who want to deepen clinical and research expertise beyond entry-level licensure.", credits=30),
]

# ── The Fletcher School of Law and Diplomacy ──
PROGRAMS += [
    _p("tufts-fletcher-maia", _FLETCHER, "Master of Arts in International Affairs", "International Affairs", "masters", 24,
       "The Fletcher School of Law and Diplomacy", "45.09",
       "The Fletcher School's flagship two-year professional degree (formerly the MALD), offering a flexible, self-designed curriculum across diplomacy, security, development, and international law and business.",
       "Early-career professionals pursuing global careers in diplomacy, security, development, or international business who want a flexible, interdisciplinary graduate degree.",
       tuition="fletcher"),
    _p("tufts-fletcher-mib", _FLETCHER, "Master of International Business", "International Business", "masters", 24,
       "The Fletcher School of Law and Diplomacy", "52.11",
       "A graduate business degree grounded in global markets, finance, and strategy for careers at the intersection of business and international affairs.",
       "Professionals aiming for global business, finance, or development careers who want business training embedded in international affairs.",
       tuition="fletcher"),
    _p("tufts-fletcher-msie", _FLETCHER, "Master of Science in International Economics", "International Economics", "masters", 12,
       "The Fletcher School of Law and Diplomacy", "45.06",
       "A focused graduate degree in international and development economics for careers in economic policy and analysis.",
       "Graduates focused on economic policy and development who want a specialized international-economics master's.",
       tuition="fletcher"),
    _p("tufts-fletcher-mscpp", _FLETCHER, "Master of Science in Cybersecurity and Public Policy", "Cybersecurity and Public Policy", "masters", 12,
       "The Fletcher School of Law and Diplomacy", "43.01",
       "A graduate degree uniting the policy, strategy, and governance of cybersecurity with its technical foundations.",
       "Professionals working at the intersection of technology, security, and policy who want cybersecurity governance expertise.",
       tuition="fletcher"),
    _p("tufts-fletcher-llm", _FLETCHER, "Master of Laws in International Law", "International Law", "masters", 12,
       "The Fletcher School of Law and Diplomacy", "22.02",
       "An advanced law degree in public and private international law for lawyers and professionals working across borders.",
       "Law graduates and professionals who want advanced international-law training for global legal and policy careers.",
       tuition="fletcher"),
    _p("tufts-fletcher-gmap", _FLETCHER, "Executive Master of Arts in International Affairs", "International Affairs", "masters", 12,
       "The Fletcher School of Law and Diplomacy", "45.09",
       "A hybrid executive degree (formerly GMAP) for experienced professionals who study international affairs while continuing to work.",
       "Mid-career professionals with substantial experience who want a graduate international-affairs degree in a hybrid, work-compatible format.",
       delivery_format="hybrid", tuition="fletcher"),
    _p("tufts-fletcher-phd", _FLETCHER, "Doctor of Philosophy in International Affairs", "International Affairs", "phd", 60,
       "The Fletcher School of Law and Diplomacy", "45.09",
       "Doctoral research across the fields of international affairs — security, diplomacy, international law, political economy, and development.",
       "Scholars pursuing original research in international affairs and careers in academia, research, or senior policy."),
]

# ── Friedman School of Nutrition Science and Policy ──
PROGRAMS += [
    _p("tufts-friedman-ms-nutrition", _FRIEDMAN, "Master of Science in Nutrition", "Nutrition Science and Policy", "masters", 24,
       "Friedman School of Nutrition Science and Policy", "30.19",
       "Graduate study across nutrition science and policy, with specializations from biochemical and molecular nutrition to food policy and nutrition epidemiology.",
       "Students building careers in nutrition science, dietetics, food policy, or global nutrition who want the country's only dedicated nutrition graduate school."),
    _p("tufts-friedman-phd-nutrition", _FRIEDMAN, "Doctor of Philosophy in Nutrition", "Nutrition", "phd", 60,
       "Friedman School of Nutrition Science and Policy", "30.19",
       "Doctoral research spanning molecular nutrition, nutritional epidemiology, food systems, and nutrition policy.",
       "Scholars pursuing original nutrition research and careers in academia, government, or global nutrition and food policy."),
]

# ── School of Medicine (+ Public Health & Graduate School of Biomedical Sciences) ──
PROGRAMS += [
    _p("tufts-md", _MED, "Doctor of Medicine", "Medicine", "professional", 48,
       "Tufts University School of Medicine", "51.12",
       "The professional degree preparing physicians through integrated biomedical science, clinical training, and patient care.",
       "Students committed to becoming physicians who want rigorous clinical and scientific training at an established medical school.",
       tuition=74118),
    _p("tufts-mph", _MED, "Master of Public Health", "Public Health", "masters", 24,
       "Tufts University School of Medicine", "51.22",
       "Professional training in the science and practice of public health — epidemiology, health policy, and program design.",
       "Students and clinicians committed to population health who want applied public-health training across research and practice."),
    _p("tufts-physician-assistant-ms", _MED, "Master of Science in Physician Assistant Studies", "Physician Assistant Studies", "masters", 24,
       "Tufts University School of Medicine", "51.09",
       "Professional training preparing physician assistants for clinical practice across medical specialties.",
       "Students entering the physician-assistant profession who want clinically intensive training toward certification and practice."),
    _p("tufts-health-informatics-ms", _MED, "Master of Science in Health Informatics and Analytics", "Health Informatics and Analytics", "masters", 24,
       "Tufts University School of Medicine", "51.27",
       "An online master's applying data science and informatics to health care, from clinical data to analytics and decision support.",
       "Health and technology professionals who want to apply data and informatics to improve health-care systems and outcomes.",
       delivery_format="online"),
    _p("tufts-biomedical-sciences-ms", _MED, "Master of Science in Biomedical Sciences", "Biomedical Sciences", "masters", 12,
       "Graduate School of Biomedical Sciences", "26.02",
       "A one-year special master's strengthening biomedical foundations for students preparing for medical and health-professional study.",
       "Post-baccalaureate students strengthening their science record and preparation before applying to medical or health-professional programs."),
    _p("tufts-gsbs-gmcb-phd", _MED, "Doctor of Philosophy in Genetics, Molecular and Cellular Biology", "Genetics, Molecular and Cellular Biology", "phd", 60,
       "Graduate School of Biomedical Sciences", "26.04",
       "Doctoral research spanning genetics, molecular biology, and cell and developmental biology in a health-sciences setting.",
       "Scholars pursuing original research in molecular and cellular life science toward academic or biomedical-industry careers."),
    _p("tufts-gsbs-immunology-phd", _MED, "Doctor of Philosophy in Immunology", "Immunology", "phd", 60,
       "Graduate School of Biomedical Sciences", "26.05",
       "Doctoral research on the immune system in health and disease, from molecular immunology to infection and inflammation.",
       "Scholars pursuing original immunology research and careers in academic or biomedical research."),
    _p("tufts-gsbs-microbiology-phd", _MED, "Doctor of Philosophy in Molecular Microbiology", "Molecular Microbiology", "phd", 60,
       "Graduate School of Biomedical Sciences", "26.05",
       "Doctoral research on microbes and host-pathogen interactions, from bacterial pathogenesis to microbial genetics.",
       "Scholars pursuing original microbiology research toward academic, public-health, or industry careers."),
    _p("tufts-gsbs-neuroscience-phd", _MED, "Doctor of Philosophy in Neuroscience", "Neuroscience", "phd", 60,
       "Graduate School of Biomedical Sciences", "26.15",
       "Doctoral research on the nervous system, from molecular and cellular neuroscience to systems and behavior.",
       "Scholars pursuing original neuroscience research and careers in academic or biomedical research."),
    _p("tufts-gsbs-cts-ms", _MED, "Master of Science in Clinical and Translational Science", "Clinical and Translational Science", "masters", 24,
       "Graduate School of Biomedical Sciences", "51.14",
       "Graduate training in the methods that move discoveries from laboratory to clinic — study design, biostatistics, and translational research.",
       "Clinicians and researchers who want rigorous methods training to lead clinical and translational studies.", credits=30),
    _p("tufts-gsbs-cts-phd", _MED, "Doctor of Philosophy in Clinical and Translational Science", "Clinical and Translational Science", "phd", 60,
       "Graduate School of Biomedical Sciences", "51.14",
       "Doctoral research in the science of translating biomedical discovery into clinical and population health impact.",
       "Physician-scientists and researchers pursuing original translational research and academic-medicine careers."),
]

# ── School of Dental Medicine ──
PROGRAMS += [
    _p("tufts-dmd", _DENTAL, "Doctor of Dental Medicine", "Dentistry", "professional", 48,
       "Tufts University School of Dental Medicine", "51.04",
       "The professional degree preparing dentists through basic science, pre-clinical simulation, and extensive supervised patient care.",
       "Students committed to becoming dentists who want strong clinical training at one of the nation's largest dental schools.",
       tuition=104601),
    _p("tufts-dental-research-ms", _DENTAL, "Master of Science in Dental Research", "Dental Research", "masters", 24,
       "Tufts University School of Dental Medicine", "51.05",
       "Graduate research training in oral and craniofacial science, often paired with postgraduate specialty education.",
       "Dentists and researchers advancing oral-health science who want formal research training alongside clinical specialization.", credits=30),
]

# ── Cummings School of Veterinary Medicine ──
PROGRAMS += [
    _p("tufts-dvm", _VET, "Doctor of Veterinary Medicine", "Veterinary Medicine", "professional", 48,
       "Cummings School of Veterinary Medicine", "01.80",
       "The professional degree preparing veterinarians through biomedical science and clinical training across companion, farm, and wildlife species.",
       "Students committed to becoming veterinarians who want comprehensive clinical training at New England's only veterinary school.",
       tuition=68908),
    _p("tufts-mapp-ms", _VET, "Master of Science in Animals and Public Policy", "Animals and Public Policy", "masters", 12,
       "Cummings School of Veterinary Medicine", "01.81",
       "Graduate study of the ethical, policy, and societal dimensions of human-animal relationships.",
       "Advocates and professionals focused on animal welfare and policy who want interdisciplinary graduate training.", credits=30),
    _p("tufts-conservation-medicine-ms", _VET, "Master of Science in Conservation Medicine", "Conservation Medicine", "masters", 12,
       "Cummings School of Veterinary Medicine", "01.81",
       "An interdisciplinary master's linking animal, human, and ecosystem health under a One Health framework.",
       "Professionals working at the intersection of wildlife, ecosystem, and public health who want One Health training.", credits=30),
    _p("tufts-idgh-ms", _VET, "Master of Science in Infectious Disease and Global Health", "Infectious Disease and Global Health", "masters", 12,
       "Cummings School of Veterinary Medicine", "01.81",
       "Graduate study of infectious disease across species and populations, integrating microbiology, epidemiology, and global health.",
       "Students focused on infectious disease and global health who want a One Health, cross-species foundation.", credits=30),
    _p("tufts-comparative-biomedical-phd", _VET, "Doctor of Philosophy in Comparative Biomedical Sciences", "Comparative Biomedical Sciences", "phd", 60,
       "Cummings School of Veterinary Medicine", "01.81",
       "Doctoral research in animal and comparative biomedical science, from infectious disease to clinical and pathological sciences.",
       "Scholars pursuing original research in comparative and veterinary biomedical science toward academic or research careers."),
]

# ── SMFA at Tufts — graduate ──
PROGRAMS += [
    _p("tufts-mfa", _SMFA, "Master of Fine Arts", "Studio Art", "masters", 24,
       "School of the Museum of Fine Arts at Tufts", "50.07",
       "An interdisciplinary studio-art terminal degree grounded in independent practice across media, critique, and critical theory.",
       "Practicing artists pursuing the terminal studio degree who want an open, cross-media MFA within a research university."),
    _p("tufts-art-education-mat", _SMFA, "Master of Arts in Teaching in Art Education", "Art Education", "masters", 12,
       "School of the Museum of Fine Arts at Tufts", "13.13",
       "Graduate preparation for art educators, combining studio practice, pedagogy, and pathways toward teacher licensure.",
       "Artists who want to teach who need studio depth, pedagogy, and a route to art-education licensure."),
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# ── Tuition ────────────────────────────────────────────────────────────────
_TUITION_UG = 70704  # Tufts undergraduate tuition, 2025-26 (Tufts Student Financial Services)
_GRAD_PER_CREDIT = 1799  # Tufts School of Arts & Sciences / Engineering graduate rate per credit, 2025-26
_FLETCHER_ANNUAL = 61450  # The Fletcher School residential master's annual tuition, 2026-27
_TUITION_RATES_URL = "https://students.tufts.edu/financial-services"
_GRAD_RATES_URL = "https://asegrad.tufts.edu/tuition-aid/tuition-and-fees"
_FLETCHER_RATES_URL = "https://fletcher.tufts.edu/admissions/financing-your-education/tuition-expenses"

# Schools that bill graduate tuition at their own (unverified-this-pass) rate → honest
# cost omission rather than a guessed figure. These master's programs carry no annual scalar.
_TUITION_OMIT_SCHOOLS = {_FRIEDMAN, _MED, _SMFA}
_TUITION_OMIT_REASON = (
    "This program is billed at its school's own published graduate tuition rate, which was "
    "not independently verified to two sources at author time; rather than guess an annual "
    "figure, the matcher tuition scalar is honestly omitted (see the program's official "
    "tuition page). Tufts School of Arts & Sciences and Engineering graduate programs bill "
    "$1,799 per credit (2025-26); professional-school rates differ by school."
)


def _grad_cost(spec: dict) -> dict | None:
    """Annual grad tuition from the verified AS&E per-credit rate × credits ÷ program-years."""
    if spec.get("tuition") == "fletcher":
        return {
            "tuition_usd": _FLETCHER_ANNUAL,
            "funded": False,
            "basis": "The Fletcher School published residential master's annual tuition (2026-27)",
            "source": "The Fletcher School — Tuition & Expenses",
            "source_url": _FLETCHER_RATES_URL,
            "year": "2026-27",
        }
    if spec["school"] in (_AS, _ENG) and spec["degree_type"] == "masters":
        credits = spec.get("credits", 30)
        years = (spec.get("duration_months") or 24) / 12
        total = _GRAD_PER_CREDIT * credits
        annual = round(total / years)
        return {
            "tuition_usd": annual,
            "funded": False,
            "per_credit_usd": _GRAD_PER_CREDIT,
            "degree_credits": credits,
            "program_years": round(years, 2),
            "total_program_usd": total,
            "basis": "Annualized from Tufts' published AS&E per-credit graduate rate x degree credits / program years",
            "source": "Tufts School of Arts & Sciences / Engineering — Graduate Tuition (per credit, 2025-26)",
            "source_url": _GRAD_RATES_URL,
            "year": "2025-26",
        }
    return None


def _resolve_tuition(spec: dict) -> int | None:
    if isinstance(spec.get("tuition"), int):
        return spec["tuition"]
    dt = spec["degree_type"]
    if dt == "bachelors":
        return _TUITION_UG
    if dt == "phd":
        return 0  # AS&E/GSAS research doctorates fully funded by a Tufts tuition scholarship
    cost = _grad_cost(spec)
    if cost is not None:
        return cost["tuition_usd"]
    return None  # professional (MD/DMD/DVM have explicit overrides) or omitted school


def _has_tuition(spec: dict) -> bool:
    return _resolve_tuition(spec) is not None or spec["degree_type"] == "phd"


# ── external_reviews (MBAn shape) — GATHERED → SUMMARIZED → CITED ──────────────
_REV_DISCLAIMER = (
    "Themes are aggregated and paraphrased from public third-party coverage and the "
    "school's own published outcomes — not individual verbatim quotes or ratings."
)


def _reviews(summary: str, themes: list[tuple], sources: list[tuple]) -> dict:
    return {
        "summary": summary,
        "themes": [{"label": lbl, "sentiment": s, "detail": d} for (lbl, s, d) in themes],
        "sources": [{"label": lbl, "url": u} for (lbl, u) in sources],
        "disclaimer": _REV_DISCLAIMER,
    }


_REVIEWS_BY_SLUG: dict[str, dict] = {
    "tufts-fletcher-maia": _reviews(
        "The Fletcher School's Master of Arts in International Affairs (long known as the MALD) is one of "
        "the oldest and most respected professional degrees in international affairs, prized for its "
        "flexible, self-designed curriculum and tight-knit global alumni network; cost and the pivot to "
        "a renamed degree are the main discussion points.",
        [
            ("Flexible, self-designed curriculum", "positive", "Students and observers highlight Fletcher's unusually flexible structure, letting each student build a cross-disciplinary field-of-study mix across security, development, law, and business."),
            ("Strong global network", "positive", "Foreign Policy and other rankings have historically placed Fletcher among the top U.S. schools for a policy/IR master's, with an influential alumni network in diplomacy, multilaterals, and NGOs."),
            ("Established reputation", "positive", "Founded in 1933, Fletcher is the oldest graduate school of international affairs in the U.S., a signal that carries weight with employers in the field."),
            ("Cost and funding", "caution", "As a private professional degree, tuition and Boston living costs are high, and full funding is competitive — a common consideration prospective students weigh."),
            ("Degree rename", "mixed", "The signature MALD was recently renamed the Master of Arts in International Affairs; the curriculum is continuous, but applicants should note the new name across older sources."),
        ],
        [
            ("The Fletcher School — Master of Arts in International Affairs", "https://fletcher.tufts.edu/academics/degrees-programs"),
            ("Foreign Policy — Top IR schools (professional master's)", "https://foreignpolicy.com/"),
            ("The Fletcher School — Tuition & Expenses", "https://fletcher.tufts.edu/admissions/financing-your-education/tuition-expenses"),
        ],
    ),
    "tufts-md": _reviews(
        "Tufts University School of Medicine is an established private medical school with strong clinical "
        "training in the Boston area and a broad affiliated-hospital network; high cost of attendance is the "
        "most consistent caution.",
        [
            ("Clinical training network", "positive", "Students train across a wide network of affiliated hospitals in and beyond Boston, giving broad exposure to clinical settings."),
            ("Established, well-regarded school", "positive", "U.S. News ranks Tufts among ranked U.S. medical schools for both research and primary care, and the M.D. carries a long-standing reputation in the Northeast."),
            ("Integrated, supportive curriculum", "positive", "Reviewers describe an integrated preclinical curriculum and a collaborative, student-supportive culture."),
            ("Cost of attendance", "caution", "As a private medical school, tuition and Boston living costs are high; students should plan carefully for debt load."),
            ("Large class and city setting", "mixed", "A relatively large class in an urban setting suits many students but is a fit consideration for those seeking a smaller or rural program."),
        ],
        [
            ("U.S. News — Tufts University School of Medicine", "https://www.usnews.com/best-graduate-schools/top-medical-schools/tufts-university-04101"),
            ("Tufts School of Medicine — Tuition & Fees", "https://medicine.tufts.edu/admissions-financial-aid/tuition-fees/tuition-fees"),
            ("Tufts University School of Medicine — MD program", "https://medicine.tufts.edu/academics/md-programs"),
        ],
    ),
    "tufts-dvm": _reviews(
        "The Cummings School is the only veterinary school in New England and is well regarded for clinical "
        "training, wildlife and conservation medicine, and its Foster Hospital for Small Animals; cost is the "
        "main caution.",
        [
            ("Only vet school in New England", "positive", "Cummings is the sole veterinary school in the region, with a large caseload through the Foster Hospital for Small Animals and a large-animal hospital."),
            ("Breadth across species and One Health", "positive", "Students gain exposure across companion, farm, wildlife, and conservation medicine, with distinctive programs in international veterinary medicine and One Health."),
            ("Strong clinical reputation", "positive", "U.S. News ranks Cummings among the ranked U.S. veterinary programs, and its teaching hospitals give hands-on clinical depth."),
            ("Cost of attendance", "caution", "Veterinary tuition and living costs are high relative to typical veterinary starting salaries — an important debt consideration."),
            ("Rural campus", "mixed", "The Grafton, Massachusetts campus offers space and large-animal facilities but is a fit consideration for students who prefer an urban setting."),
        ],
        [
            ("U.S. News — Best Veterinary Schools", "https://www.usnews.com/best-graduate-schools/top-veterinary-schools/vet-rankings"),
            ("Cummings School — DVM program", "https://vet.tufts.edu/dvm-program-overview"),
            ("Cummings School — Cost & financial aid", "https://vet.tufts.edu/admissions/tuition-costs-financial-aid"),
        ],
    ),
    "tufts-friedman-ms-nutrition": _reviews(
        "The Friedman School is the only graduate school in the U.S. devoted solely to nutrition, respected for "
        "bridging biomedical nutrition science with food and nutrition policy; its specialized focus is both its "
        "strength and a fit consideration.",
        [
            ("Only U.S. nutrition graduate school", "positive", "Friedman is uniquely dedicated to nutrition, spanning molecular nutrition, epidemiology, food systems, and policy under one roof."),
            ("Science-plus-policy breadth", "positive", "Students can move between biomedical nutrition science and food/nutrition policy, an unusual range for a single school."),
            ("Research strength", "positive", "Ties to the Jean Mayer USDA Human Nutrition Research Center on Aging and the Feinstein International Center give strong research and global-nutrition connections."),
            ("Specialized scope", "caution", "The dedicated focus on nutrition is a strength for committed students but a fit consideration for those wanting a broader public-health degree."),
            ("Cost and funding", "mixed", "As a private graduate program, funding varies by specialization and is competitive — applicants should weigh cost against career goals."),
        ],
        [
            ("Friedman School — Degrees & Programs", "https://nutrition.tufts.edu/academics/degrees-programs"),
            ("U.S. News — Best Colleges (Tufts University)", "https://www.usnews.com/best-colleges/tufts-university-2219"),
            ("Jean Mayer USDA Human Nutrition Research Center on Aging", "https://hnrca.tufts.edu/"),
        ],
    ),
}


def _outcomes_kind(spec: dict) -> str:
    if spec["degree_type"] in ("bachelors", "masters", "phd", "professional"):
        return "institution"
    return "none"


def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["tracks"] if "tracks" not in spec else []
    omitted += [
        "class_profile.cohort_size",
        "faculty_contacts.lead",
    ]
    if spec["slug"] not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if not _has_tuition(spec):
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    # Graduate/professional programs admit on program-specific cycles (no fixed date here).
    if spec["degree_type"] != "bachelors":
        omitted.append("application_requirements.deadlines")
    omitted.append("outcomes_data.employment_rate")
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Tufts University to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Tufts University is absent — safe on fresh/CI databases.
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
    # Lead media_gallery with the verified hero campus photo (seed's Eaton Hall),
    # preserving any existing gallery entries behind it (idempotent dedupe).
    photos = (inst.school_outcomes or {}).get("campus_photos") or []
    hero = photos[0]["url"] if photos and isinstance(photos[0], dict) else (inst.media_gallery or [None])[0]
    if hero:
        rest = [u for u in (inst.media_gallery or []) if u != hero]
        inst.media_gallery = [hero, *rest]
    inst.content_sources = dict(_INSTITUTION_CONTENT)
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
        sc.content_sources = _school_content(spec["name"])
        about = dict(_SCHOOL_ABOUT[spec["name"]])
        about["_standard"] = _standard(_ABOUT_OMITTED.get(spec["name"], []))
        sc.about_detail = about
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


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {
        p.slug: p
        for p in session.scalars(select(Program).where(Program.institution_id == inst.id))
        if p.slug
    }
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        p = existing.get(spec["slug"])
        if p is None:
            p = Program(
                institution_id=inst.id,
                program_name=spec["program_name"],
                degree_type=spec["degree_type"],
                slug=spec["slug"],
            )
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.website_url = spec.get("website") or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.content_sources = _program_content(spec)
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Tuition. Undergrad sticker; AS&E/GSAS PhDs funded (0); MD/DMD/DVM their own published
        # annual rate; Fletcher master's flat annual; AS&E/Engineering master's = per-credit rate
        # × degree credits ÷ program-years; Friedman/Med/SMFA master's omitted-with-reason.
        tuition = _resolve_tuition(spec)
        p.tuition = tuition
        grad_cost = _grad_cost(spec)
        if grad_cost is not None:
            p.cost_data = grad_cost
        elif tuition is not None:
            p.cost_data = {
                "tuition_usd": tuition,
                "funded": spec["degree_type"] == "phd",
                "source": "Tufts Student Financial Services / school tuition page",
                "source_url": _TUITION_RATES_URL,
                "year": "2025-26",
            }
        else:
            p.cost_data = {"tuition_usd": None, "omitted_reason": _TUITION_OMIT_REASON}
        # Requirements by tier / school.
        dt = spec["degree_type"]
        if spec["school"] == _FLETCHER:
            p.application_requirements = dict(_REQ_FLETCHER)
        elif spec["school"] in (_MED, _DENTAL, _VET) and dt == "professional":
            p.application_requirements = dict(_REQ_HEALTH)
        elif dt == "bachelors":
            p.application_requirements = dict(_REQ_UNDERGRAD)
        else:
            p.application_requirements = dict(_REQ_GRAD)
        # Outcomes: institution-wide Scorecard proxy for degree programs.
        if dt in ("bachelors", "masters", "phd", "professional"):
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        else:
            p.outcomes_data = None
        if p.outcomes_data is None:
            p.outcomes_data = {"_standard": _program_standard(spec)}
        else:
            p.outcomes_data["_standard"] = _program_standard(spec)
        p.cip_code = spec["cip"]
        p.who_its_for = spec["who"]
        if "tracks" in spec:
            p.tracks = spec["tracks"]
        else:
            p.tracks = None
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(spec["slug"])
        if dt == "bachelors":
            p.application_deadline = date(2027, 1, 4)
        else:
            p.application_deadline = None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
