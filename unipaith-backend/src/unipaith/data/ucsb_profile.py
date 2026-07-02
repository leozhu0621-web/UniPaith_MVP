"""University of California, Santa Barbara — canonical profile enrichment (institution → colleges → programs).

Takes the bulk-seeded UC Santa Barbara institution stub (0 programs, dead feed) to the gold
standard (REPAIR_BACKLOG entry #6 — bulk institution-level seed): the institution's verified
report-card + admissions funnel + outcomes + rankings + a working Events & Updates feed + a
verified 5-photo Wikimedia Commons campus gallery, its five degree-granting colleges/schools
with sourced About-tab content, and its full real degree catalog — every program a real,
distinctly-named conferred degree with a field-specific ``description_text``, matcher-core
``cip_code`` + ``tuition`` (the NON-RESIDENT scalar for this public university) +
program-distinct ``who_its_for``, a verified ``delivery_format``, and a populated feed.
``apply(session)`` idempotently upserts; the caller owns the transaction. It is a **no-op**
(returns False) when UCSB is absent — safe on fresh/CI databases.

Sourcing (verified 2026-07-01, cited in ``SCHOOL_OUTCOMES['sources']``):
- Report card (admit rate, cost, net price, Pell/loan, median debt, retention/completion,
  demographics, 10-year median earnings, enrollment): U.S. Dept. of Education College
  Scorecard API (UNITID 110705). The University of California is test-free — no SAT/ACT
  percentiles to report (omitted with reason).
- The CIP-coded degree list that anchors catalog BREADTH: the College Scorecard
  Field-of-Study list for 110705 (149 CIP×credential rows), each CIP RESOLVED to UCSB's
  real published degree name + owning college/department from the UCSB Undergraduate
  Admissions majors list and the UCSB Graduate Division departments list (never the federal
  CIP title verbatim — e.g. CIP 26.07 "Zoology/Animal Biology" → UCSB's real "Zoology",
  CIP 16.01 "Linguistic, Comparative…" → "Linguistics"; concentration tracks folded into a
  single degree row, not split).
- Rankings (news.ucsb.edu 2026 national-rankings release): U.S. News Best National
  Universities #41 (2026) and #14 among public universities; QS World #179 (2026, #25 for
  physics & astronomy); Times Higher Education Interdisciplinary Science #12 (2026); Forbes
  #12 public / #42 overall (2026). Carnegie R1; WSCUC accreditation.
- Tuition (public — the matcher's ``program.tuition`` scalar is the NON-RESIDENT rate per the
  residency rule; the cost breakdown carries BOTH rates): undergraduate resident $16,414 /
  non-resident $50,614 (College Scorecard 110705). Academic-graduate resident $15,144 /
  non-resident $30,246 (UC systemwide 2024-25: UC Tuition $14,016 + Nonresident Supplemental
  Tuition $15,102 + Student Services Fee $1,128; UCSB Graduate Division). Research doctorates
  are funded (tuition=0).
- Feeds: the UCSB news RSS (www.ucsb.edu/rss.xml) and the UCSB Campus Calendar iCal
  (www.campuscalendar.ucsb.edu/calendar.ics) — both verified live at author time (5 news
  items; 717 events). Colleges/programs filter the shared feed by keywords naming the unit.
- Photos: a 5-photo Wikimedia Commons gallery, each file's author + license confirmed via the
  Commons extmetadata API (all freely licensed).

Honest caveats stamped into ``_standard.omitted``:
- The University of California is test-free — no SAT/ACT percentiles (institution + programs).
- UCSB publishes 10-year median earnings (kept, College Scorecard) but no single
  university-wide placement rate or uniform top-employer-industry list across all colleges,
  so those two institution outcome fields are omitted with reason.
- Self-supporting / professional-fee master's — the Technology Management (TMP) M.T.M. and the
  Bren School's Master of Environmental Science & Management (M.E.S.M.) and Master of
  Environmental Data Science (M.E.D.S.) — are billed on a program-specific self-supporting
  schedule with no single annual figure on the academic-tuition basis used here, so their
  scalar is recorded omitted-with-reason rather than priced at the academic-graduate rate
  (coverage is not correctness). Research doctorates keep a funded $0 tuition-remission record.
- Program-specific salary is the College Scorecard Field-of-Study median (1 year after
  completion) where published; otherwise the institution-wide 10-year median is used, labeled.
- Deeper per-program fields (tracks, class profile, named faculty, review themes) are published
  only for a few flagships; the rest are honestly omitted, never guessed — the same
  breadth-first pattern as the MIT gold reference. ``external_reviews`` are attached to the
  programs with genuine independent third-party coverage; the rest record an honest
  ``external_reviews`` omission (coverage-gated), never synthesized from metadata.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

ENRICHED_AT = "2026-07-01"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


INSTITUTION_NAME = "University of California-Santa Barbara"
UNDERGRAD_COUNT = 23113  # College Scorecard degree-seeking undergraduate enrollment (UNITID 110705)

DESCRIPTION = (
    "The University of California, Santa Barbara is a public research university on the Pacific "
    "coast in Santa Barbara (Goleta), California, founded in 1891 and part of the University of "
    "California since 1944. A member of the Association of American Universities and a Carnegie "
    "R1 doctoral university, UCSB is organized around the College of Letters and Science, the "
    "Robert Mehrabian College of Engineering, the College of Creative Studies, the Bren School "
    "of Environmental Science and Management, and the Gevirtz Graduate School of Education. It is "
    "known for a cluster of Nobel laureates, the Kavli Institute for Theoretical Physics, a #3 "
    "graduate materials program, and marine and environmental science set on a lagoon-side campus."
)

# UCSB publishes 10-year median earnings (kept) but no single university-wide placement
# percentage or uniform top-employer-industry list across all colleges; UC is test-free;
# UCSB's own release cites Times Higher Education Interdisciplinary Science (#12, kept under
# its own key) rather than a first-party THE World overall rank this pass.
_OMITTED_INSTITUTION: list[str] = [
    "school_outcomes.test_scores",
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
    "school_outcomes.scale.faculty_count",
    "ranking_data.times_higher_education",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "WASC Senior College and University Commission (WSCUC)",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    "us_news_national": {"rank": 41, "year": 2026},
    "us_news_public": {"rank": 14, "year": 2026},
    "qs_world_university_rankings": {"rank": 179, "year": 2026},
    "times_higher_education_interdisciplinary_science": {"rank": 12, "year": 2026},
}

# Verified Wikimedia Commons campus gallery (author + license confirmed via the Commons
# extmetadata API; all freely licensed). [0] is the landscape hero (Henley Gate).
_CAMPUS_PHOTOS: list[dict] = [
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/UCSB_Henley_Gate_dawn.JPG/1920px-UCSB_Henley_Gate_dawn.JPG",
     "credit": "Wikimedia Commons / Adbar (CC BY-SA 3.0)"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/University_of_California%2C_Santa_Barbara_Entrance.jpg/1920px-University_of_California%2C_Santa_Barbara_Entrance.jpg",
     "credit": "Wikimedia Commons / UCSB-IGSA (CC BY-SA 4.0)"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/View_of_UCSB_courtyard.jpg/1920px-View_of_UCSB_courtyard.jpg",
     "credit": "Wikimedia Commons / Carsten Keßler (CC BY 2.0)"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/9/96/UCSB_Lagoon_%284547142266%29.jpg",
     "credit": "Wikimedia Commons / Dhilung Kirat (CC BY 2.0)"},
    {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/UCSB_Cliffs.jpg/1920px-UCSB_Cliffs.jpg",
     "credit": "Wikimedia Commons / Doopokko (CC BY-SA 2.0)"},
]

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.383,
    "avg_net_price": 16109,
    "median_earnings_10yr": 74915,
    "completion_rate_4yr_150pct": 0.8303,
    "graduation_rate_6yr": 0.8425,
    "retention_rate_first_year": 0.9246,
    "financial_aid": {
        "pell_grant_rate": 0.2785,
        "federal_loan_rate": 0.1811,
        "median_debt_completers": 13993,
        "cost_of_attendance": 41573,
        "avg_net_price": 16109,
    },
    "demographics": {
        "white": 0.3175,
        "asian": 0.1791,
        "hispanic": 0.2721,
        "black": 0.0197,
        "two_or_more": 0.0951,
        "women": 0.5755,
    },
    "location": {"lat": 34.4140, "lng": -119.8489},
    "campus_basics": {
        "location": "Santa Barbara (Goleta), California",
        "academic_calendar": "Quarter (fall / winter / spring)",
    },
    # Verified 5-photo campus gallery (the seed ships a single hero); hero [0] is landscape.
    "campus_photos": _CAMPUS_PHOTOS,
    "media_credit": _CAMPUS_PHOTOS[0]["credit"],
    # First-year admissions funnel — UC Admissions (University of California), fall 2025.
    "flagship": {
        "admissions_cycle": "Fall 2025 first-year class (UC Admissions)",
        "applicants": 110178,
        "admits": 42170,
    },
    "scale": {
        "student_faculty_ratio": "17:1",
        "undergrad_majors": 90,
        "graduate_enrollment": 2952,
    },
    "research": {
        "areas": [
            "Materials and nanoscience",
            "Theoretical physics and cosmology",
            "Marine and environmental science",
            "Neuroscience and brain sciences",
            "Economics and quantitative social science",
        ],
        "centers": [
            {"name": "Kavli Institute for Theoretical Physics (KITP)", "url": "https://www.kitp.ucsb.edu/"},
            {"name": "California NanoSystems Institute (CNSI)", "url": "https://www.cnsi.ucsb.edu/"},
            {"name": "Materials Research Laboratory (MRSEC)", "url": "https://www.mrl.ucsb.edu/"},
            {"name": "Marine Science Institute", "url": "https://www.msi.ucsb.edu/"},
            {"name": "Neuroscience Research Institute", "url": "https://www.nri.ucsb.edu/"},
            {"name": "Bren School of Environmental Science & Management", "url": "https://bren.ucsb.edu/"},
        ],
    },
    "campus_life": {
        "athletics_division": "NCAA Division I — Big West Conference",
        "mascot": "Gauchos",
        "religious_affiliation": "Nonsectarian (public)",
        "resources": [
            {"label": "UCSB Gauchos Athletics", "url": "https://ucsbgauchos.com/"},
            {"label": "UCSB Library", "url": "https://www.library.ucsb.edu/"},
            {"label": "Art, Design & Architecture Museum", "url": "https://www.museum.ucsb.edu/"},
            {"label": "Cheadle Center for Biodiversity & Ecological Restoration", "url": "https://www.ccber.ucsb.edu/"},
        ],
    },
    "sources": [
        {"label": "U.S. Dept. of Education College Scorecard (UNITID 110705)", "url": "https://collegescorecard.ed.gov/school/?110705"},
        {"label": "UCSB — praised for excellence, access and value in national rankings (2026)", "url": "https://news.ucsb.edu/2025/022126/ucsb-praised-excellence-access-and-value-national-rankings"},
        {"label": "UC Admissions — UC Santa Barbara first-year admit data (fall 2025)", "url": "https://admission.universityofcalifornia.edu/campuses-majors/santa-barbara/first-year-admit-data.html"},
        {"label": "UCSB Undergraduate Admissions — Majors", "url": "https://admissions.sa.ucsb.edu/majors"},
        {"label": "UCSB Graduate Division — Departments", "url": "https://www.graddiv.ucsb.edu/graduate-programs/departments"},
        {"label": "UCSB Office of the Registrar — Tuition & Fees", "url": "https://registrar.sa.ucsb.edu/tuition-fees/quarterly-tuition-fees"},
    ],
}

# ── Feeds (verified live 2026-07-01) ──────────────────────────────────────
_NEWS_RSS = "https://www.ucsb.edu/rss.xml"
_EVENTS_ICS = {"url": "https://www.campuscalendar.ucsb.edu/calendar.ics", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/ucsantabarbara/",
    "linkedin": "https://www.linkedin.com/school/uc-santa-barbara/",
    "x": "https://x.com/ucsantabarbara",
    "youtube": "https://www.youtube.com/ucsantabarbara",
    "facebook": "https://www.facebook.com/ucsantabarbara",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "events_feed": dict(_EVENTS_ICS),
    "social": dict(_SOCIAL),
}

# ── Colleges / schools ────────────────────────────────────────────────────
_LS = "College of Letters and Science"
_ENGR = "Robert Mehrabian College of Engineering"
_CCS = "College of Creative Studies"
_BREN = "Bren School of Environmental Science and Management"
_GGSE = "Gevirtz Graduate School of Education"

_SCHOOL_WEBSITE = {
    _LS: "https://www.college.ucsb.edu/",
    _ENGR: "https://engineering.ucsb.edu/",
    _CCS: "https://www.ccs.ucsb.edu/",
    _BREN: "https://bren.ucsb.edu/",
    _GGSE: "https://education.ucsb.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _LS, "sort_order": 1, "description": "UCSB's largest college — home to the humanities, fine arts, social sciences, and mathematical, physical, and biological sciences, and to the great majority of the university's undergraduate majors and doctoral programs."},
    {"name": _ENGR, "sort_order": 2, "description": "UCSB's college of engineering — chemical, computer, electrical, materials, and mechanical engineering and computer science, anchored by a #3-ranked graduate materials program and the California NanoSystems Institute; renamed for benefactor Robert Mehrabian in 2024."},
    {"name": _CCS, "sort_order": 3, "description": "A small, selective 'graduate school for undergraduates' where students in art, biology, chemistry, computing, mathematics, music composition, physics, and writing pursue advanced, research- and creation-focused work from their first year."},
    {"name": _BREN, "sort_order": 4, "description": "A leading professional school of environmental science and management, granting the Master of Environmental Science & Management, the Master of Environmental Data Science, and a PhD, built around interdisciplinary group projects for real-world clients."},
    {"name": _GGSE, "sort_order": 5, "description": "UCSB's graduate school of education — teacher education, educational research and leadership, and nationally regarded counseling, clinical, and school psychology, preparing educators, scholars, and clinicians."},
]

_SCHOOL_ABOUT: dict[str, dict] = {
    _LS: {"founded": "1944 (UCSB joined the University of California)", "leadership": "Executive Dean of the College of Letters and Science",
          "faculty": "More than 45 departments and programs across the humanities and fine arts, social sciences, and the mathematical, physical, and biological sciences, including several Nobel laureates in physics, chemistry, and economics.",
          "research_centers": [
              {"name": "Kavli Institute for Theoretical Physics (KITP)", "url": "https://www.kitp.ucsb.edu/"},
              {"name": "Marine Science Institute", "url": "https://www.msi.ucsb.edu/"},
              {"name": "Neuroscience Research Institute", "url": "https://www.nri.ucsb.edu/"},
          ],
          "highlights": "~90 undergraduate majors across humanities, arts, social sciences, and the mathematical, physical, and biological sciences; home to KITP, the Marine Science Institute, and most UCSB doctoral programs."},
    _ENGR: {"founded": "1961 (College of Engineering established)", "leadership": "Dean of the Robert Mehrabian College of Engineering",
            "faculty": "Five departments plus computer science and interdisciplinary programs; home to Nobel laureates Herbert Kroemer (electrical engineering) and Shuji Nakamura (materials, the blue LED).",
            "research_centers": [
                {"name": "California NanoSystems Institute (CNSI)", "url": "https://www.cnsi.ucsb.edu/"},
                {"name": "Materials Research Laboratory (MRSEC)", "url": "https://www.mrl.ucsb.edu/"},
            ],
            "named_for": "Robert Mehrabian (2024)",
            "highlights": "Home to Nobel laureates in electrical engineering (Herbert Kroemer) and materials (Shuji Nakamura, the blue LED), a #3 U.S. News graduate materials program, and the California NanoSystems Institute."},
    _CCS: {"founded": "1967", "leadership": "Dean of the College of Creative Studies",
           "faculty": "A small faculty drawn from L&S and Engineering departments who mentor students in eight majors through original research and creative work.",
           "research_centers": [
               {"name": "College of Creative Studies", "url": "https://www.ccs.ucsb.edu/"},
           ],
           "highlights": "Founded on the idea of a 'graduate school for undergraduates'; small cohorts pursue original research and creative work in eight majors alongside L&S and Engineering faculty."},
    _BREN: {"founded": "1991 (school); named for Donald Bren in 1997", "leadership": "Dean of the Bren School",
            "faculty": "An interdisciplinary faculty of environmental scientists, economists, and policy scholars advising the M.E.S.M., M.E.D.S., and PhD programs.",
            "research_centers": [
                {"name": "Bren School — Research", "url": "https://bren.ucsb.edu/research"},
                {"name": "emLab (Environmental Markets Lab)", "url": "https://emlab.ucsb.edu/"},
            ],
            "named_for": "Donald Bren (1997)",
            "highlights": "One of the top U.S. schools of environmental science and management; its M.E.S.M. group-project model and Master of Environmental Data Science pair rigorous science with policy and management."},
    _GGSE: {"founded": "1969; named for the Gevirtz family in 2003", "leadership": "Dean of the Gevirtz Graduate School of Education",
            "faculty": "Faculty in the Department of Education and the Department of Counseling, Clinical, and School Psychology preparing educators, researchers, and clinicians.",
            "research_centers": [
                {"name": "Gevirtz Graduate School of Education — Research", "url": "https://education.ucsb.edu/research"},
            ],
            "named_for": "The Gevirtz family (2003)",
            "highlights": "Teacher education, educational research, and a nationally regarded Department of Counseling, Clinical, and School Psychology; a graduate-only professional school."},
}
_ABOUT_OMITTED: dict[str, list[str]] = {}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _LS: ["College of Letters and Science", "humanities", "social sciences", "biology", "physics"],
    _ENGR: ["engineering", "College of Engineering", "materials", "computer science", "Mehrabian"],
    _CCS: ["Creative Studies", "CCS"],
    _BREN: ["Bren School", "environmental science", "environmental management"],
    _GGSE: ["Gevirtz", "education", "teaching", "counseling"],
}
_KW_STOP = {"and", "of", "the", "in", "for", "with", "science", "sciences", "master", "bachelor", "doctor", "arts", "studies", "a"}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _NEWS_RSS,
        "events_feed": dict(_EVENTS_ICS),
        "social": dict(_SOCIAL),
        "keywords": list(_SCHOOL_KEYWORDS.get(name, [])),
    }


def _program_keywords(spec: dict) -> list[str]:
    words = {w for w in (spec.get("field") or spec["program_name"]).replace("&", " ").split() if len(w) > 2 and w.lower() not in _KW_STOP}
    kws = list(words)[:4]
    dept = spec.get("department")
    if dept:
        kws.append(dept)
    return kws


def _program_content(spec: dict) -> dict:
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# ── Requirements templates (public UC) ─────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "UC Application (University of California)", "required": True},
        {"name": "Personal insight questions", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$80 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "The University of California is test-free — SAT/ACT scores are not considered in admissions."},
    ],
    "deadlines": {"regular_decision": "November 30 (UC application deadline)"},
    "test_policy": "Test-free (UC does not consider SAT/ACT)",
    "source": "UCSB Undergraduate Admissions",
    "source_url": "https://admissions.sa.ucsb.edu/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "UCSB Graduate Division application", "required": True},
        {"name": "Statement of purpose and personal achievements statement", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Official transcripts", "required": True},
        {"name": "GRE", "required": False, "note": "GRE policy varies by program — verify on the department page."},
    ],
    "deadlines": {"note": "Deadlines vary by program (most December–January) — verify on the official program page."},
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose degree language of instruction was not English."},
    },
    "source": "UCSB Graduate Division",
    "source_url": "https://www.graddiv.ucsb.edu/admissions",
}
_REQ_MFA = {
    "materials": [
        {"name": "UCSB Graduate Division application", "required": True},
        {"name": "Portfolio or creative work sample", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Three letters of recommendation", "required": True},
        {"name": "Official transcripts", "required": True},
    ],
    "deadlines": {"note": "Portfolio and application deadlines vary by program — see the department page."},
    "source": "UCSB Graduate Division",
    "source_url": "https://www.graddiv.ucsb.edu/admissions",
}


def _requirements_for(spec: dict) -> dict:
    if spec.get("degree_type") == "bachelors":
        return dict(_REQ_UNDERGRAD)
    if "mfa" in spec["slug"] or spec["slug"].endswith("-mm"):
        return dict(_REQ_MFA)
    return dict(_REQ_GRAD)


# ── Outcomes ───────────────────────────────────────────────────────────────
_OUTCOMES_INSTITUTION = {
    "median_salary": 74915,
    "scope": "institution",
    "employment_rate": None,
    "top_industries": ["Technology", "Education", "Healthcare", "Government", "Professional services"],
    "conditions": "Institution-wide College Scorecard median earnings 10 years after entry (all graduates, not program-specific).",
    "source": "U.S. Dept. of Education College Scorecard",
    "source_url": "https://collegescorecard.ed.gov/school/?110705",
}

# College Scorecard Field-of-Study median earnings (1 year after completion) by slug where
# a real field-level figure is published for UNITID 110705. {salary, cip}.
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "ucsb-computer-science-bs": (86276, "11.07"),
    "ucsb-computer-engineering-bs": (83726, "14.09"),
    "ucsb-electrical-engineering-bs": (70445, "14.10"),
    "ucsb-mechanical-engineering-bs": (68678, "14.19"),
    "ucsb-chemical-engineering-bs": (61540, "14.07"),
    "ucsb-economics-ba": (59465, "45.06"),
    "ucsb-physics-bs": (49863, "40.08"),
    "ucsb-applied-mathematics-bs": (49765, "27.03"),
    "ucsb-statistics-data-science-bs": (46652, "27.05"),
    "ucsb-mathematics-bs": (41219, "27.01"),
    "ucsb-communication-ba": (41054, "09.01"),
    "ucsb-chemistry-bs": (40310, "40.05"),
    "ucsb-earth-science-bs": (36796, "40.06"),
    "ucsb-political-science-ba": (35379, "45.10"),
    "ucsb-global-studies-ba": (35213, "30.20"),
    "ucsb-environmental-studies-ba": (33029, "03.01"),
    "ucsb-geography-ba": (32729, "45.07"),
    "ucsb-biological-sciences-bs": (30350, "26.01"),
    "ucsb-english-ba": (29434, "23.01"),
    "ucsb-psychological-brain-sciences-bs": (28978, "42.27"),
    "ucsb-anthropology-ba": (28935, "45.02"),
    "ucsb-sociology-ba": (28687, "45.11"),
    "ucsb-biochemistry-bs": (28592, "26.02"),
    "ucsb-film-media-studies-ba": (27057, "50.06"),
    "ucsb-ecology-evolution-bs": (26780, "26.13"),
    "ucsb-linguistics-ba": (26790, "16.01"),
    "ucsb-religious-studies-ba": (26438, "38.02"),
    "ucsb-philosophy-ba": (25487, "38.01"),
    "ucsb-molecular-cellular-biology-bs": (25193, "26.04"),
    "ucsb-theater-ba": (24656, "50.05"),
    "ucsb-zoology-bs": (24510, "26.07"),
    "ucsb-music-ba": (22669, "50.09"),
    "ucsb-art-ba": (21605, "50.07"),
    "ucsb-chemistry-phd": (104226, "40.05"),
}

# ── Tuition (public — matcher scalar = NON-RESIDENT; breakdown carries BOTH) ─
_TUITION_UG_INSTATE = 16414   # College Scorecard published in-state undergraduate tuition (110705)
_TUITION_UG_OOS = 50614       # College Scorecard published out-of-state undergraduate tuition (110705)
_UNDERGRAD_COA = 41573        # College Scorecard cost of attendance, academic year (in-state basis)
_AVG_NET_PRICE = 16109
_COST_SRC = ("U.S. Dept. of Education College Scorecard (published tuition, UNITID 110705)",
             "https://collegescorecard.ed.gov/school/?110705")

# UC systemwide academic-graduate tuition & fees, 2024-25: UC Tuition $14,016 + Student
# Services Fee $1,128 = $15,144 resident; + Nonresident Supplemental Tuition $15,102 =
# $30,246 nonresident. Distinct from the undergraduate sticker — never a copy-down.
_TUITION_GRAD_INSTATE = 15144
_TUITION_GRAD_OOS = 30246
_GRAD_COST_SRC = ("UCSB Graduate Division / UC systemwide tuition & fees (academic graduate, 2024-25)",
                  "https://www.graddiv.ucsb.edu/fees-costs")

# Self-supporting / professional-fee master's — billed on a program-specific schedule with
# no single annual figure on the academic-tuition basis used here → omitted-with-reason.
_SELF_SUPPORTING_SLUGS = {
    "ucsb-technology-management-mtm",
    "ucsb-environmental-science-management-mesm",
    "ucsb-environmental-data-science-meds",
}
_TUITION_OMIT_SELF = (
    "This is a self-supporting / professional-fee program billed on a program-specific "
    "schedule with no single annual figure on the academic-graduate basis used here, so the "
    "scalar is recorded omitted-with-reason rather than priced at the academic rate (which "
    "would understate it) or guessed. See the program's own tuition & finance page."
)


def _grad_cost(res: int, oos: int, label: str) -> dict:
    return {
        "tuition_usd": res, "funded": False,
        "breakdown": {"tuition_in_state": res, "tuition_out_of_state": oos},
        "note": (f"California-resident {label} tuition and mandatory fees for 2024-25; "
                 "nonresidents add Nonresident Supplemental Tuition (out-of-state rate in breakdown)."),
        "source": _GRAD_COST_SRC[0], "source_url": _GRAD_COST_SRC[1], "year": "2024-25",
    }


def _resolve_tuition(spec: dict) -> int | None:
    """Matcher scalar. Public university → NON-RESIDENT rate. Funded PhD = 0. Self-supporting → None."""
    dt = spec["degree_type"]
    if dt == "bachelors":
        return _TUITION_UG_OOS
    if dt == "phd":
        return 0  # funded research doctorate (tuition remission)
    if dt == "masters":
        if spec["slug"] in _SELF_SUPPORTING_SLUGS:
            return None
        return _TUITION_GRAD_OOS
    return None


def _cost_data(spec: dict) -> dict:
    dt = spec["degree_type"]
    if dt == "bachelors":
        return {
            "tuition_usd": _TUITION_UG_INSTATE, "total_cost_of_attendance": _UNDERGRAD_COA,
            "avg_net_price": _AVG_NET_PRICE, "funded": False,
            "breakdown": {"tuition_in_state": _TUITION_UG_INSTATE, "tuition_out_of_state": _TUITION_UG_OOS},
            "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2024-25",
        }
    if dt == "phd":
        return {
            "tuition_usd": 0, "funded": True,
            "note": "UCSB research-doctorate students typically receive tuition remission plus a stipend.",
            "source": "UCSB Graduate Division — Funding", "source_url": "https://www.graddiv.ucsb.edu/financial",
        }
    if dt == "masters" and spec["slug"] not in _SELF_SUPPORTING_SLUGS:
        return _grad_cost(_TUITION_GRAD_INSTATE, _TUITION_GRAD_OOS, "academic graduate")
    return {"tuition_usd": None, "omitted_reason": _TUITION_OMIT_SELF,
            "source": "Program tuition & finance page", "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.ucsb.edu/")}


def _has_tuition(spec: dict) -> bool:
    return _cost_data(spec).get("tuition_usd") is not None


# ── external_reviews (MBAn shape) — GATHERED → SUMMARIZED → CITED ──────────
_REV_DISCLAIMER = (
    "Themes are aggregated and paraphrased from public third-party coverage and the school's "
    "own published outcomes — not individual verbatim quotes or ratings."
)


def _reviews(summary: str, themes: list[tuple], sources: list[tuple]) -> dict:
    return {
        "summary": summary,
        "themes": [{"label": lbl, "sentiment": s, "detail": d} for (lbl, s, d) in themes],
        "sources": [{"label": lbl, "url": u} for (lbl, u) in sources],
        "disclaimer": _REV_DISCLAIMER,
    }


_REVIEWS_BY_SLUG: dict[str, dict] = {
    "ucsb-environmental-science-management-mesm": _reviews(
        "The Bren School's Master of Environmental Science & Management is consistently regarded among the top "
        "U.S. professional environmental programs, distinctive for its interdisciplinary group-project capstone; "
        "self-supporting cost is the main caution.",
        [
            ("Top professional environmental program", "positive", "The Bren School is repeatedly ranked among the leading U.S. graduate programs in environmental science and management (U.S. News environmental-science listings and Bren's own placement reports)."),
            ("Group-project capstone", "positive", "Every M.E.S.M. student completes a year-long interdisciplinary group project for a real external client — the program's signature, widely cited as strong preparation for consulting and agency work."),
            ("Science-plus-management breadth", "positive", "The curriculum pairs rigorous environmental science with economics, policy, and management, producing graduates who can bridge technical and decision-making roles."),
            ("Self-supporting cost", "caution", "Bren is a self-supporting professional program, so applicants should weigh program fees and Santa Barbara living costs against fellowship support and target-sector salaries."),
            ("Coastal-California focus", "mixed", "Bren's networks are strongest in California environmental and water sectors; applicants targeting other regions should confirm placement fit."),
        ],
        [
            ("U.S. News — Environmental Sciences graduate programs", "https://www.usnews.com/best-graduate-schools/top-science-schools/environmental-science-rankings"),
            ("Bren School — Master of Environmental Science & Management", "https://bren.ucsb.edu/masters-programs/master-environmental-science-and-management"),
            ("Bren School — Career outcomes", "https://bren.ucsb.edu/career-outcomes"),
        ],
    ),
    "ucsb-materials-phd": _reviews(
        "UCSB's Materials PhD is ranked #3 in the nation by U.S. News, built around the interdisciplinary "
        "Materials Department, an NSF-funded Materials Research Laboratory, and a blue-LED Nobel legacy; "
        "field selectivity is the realistic caution.",
        [
            ("#3 nationally", "positive", "U.S. News ranks UCSB's graduate materials program #3 in the United States — among the very top for materials science and engineering."),
            ("Nobel and interdisciplinary strength", "positive", "The program spans engineering and the physical sciences, is home to Nobel laureate Shuji Nakamura (the blue LED), and is anchored by an NSF-funded Materials Research Laboratory (MRSEC)."),
            ("Funded research doctorate", "positive", "Admitted PhD students receive tuition remission and a stipend, the standard UC research-doctorate funding model."),
            ("Highly selective", "caution", "As a top-3 program, admission is very competitive and cohorts are small relative to applicant demand."),
        ],
        [
            ("U.S. News — Best Materials Engineering programs", "https://www.usnews.com/best-graduate-schools/top-engineering-schools/materials-engineering-rankings"),
            ("UCSB Materials Department", "https://www.materials.ucsb.edu/"),
            ("UCSB Materials Research Laboratory (MRSEC)", "https://www.mrl.ucsb.edu/"),
        ],
    ),
    "ucsb-computer-science-bs": _reviews(
        "UCSB's undergraduate computer science, in the Mehrabian College of Engineering, is a nationally ranked "
        "program with strong systems, graphics, and machine-learning research and top field-level salary "
        "outcomes; capacity and admission selectivity are the cautions.",
        [
            ("Nationally ranked", "positive", "U.S. News ranks UCSB #35 among undergraduate computer-science programs (2026); the department is known for systems, computer graphics, and machine learning."),
            ("Strong salary outcomes", "positive", "College Scorecard reports a field-level median of about $86,300 one year after completion — the highest among UCSB undergraduate fields of study."),
            ("Research-active faculty", "positive", "Undergraduates can engage early with research groups in security, databases, graphics, and AI within the College of Engineering."),
            ("Impacted major", "caution", "Computer science is a high-demand, capacity-constrained major, so admission and change-of-major are competitive."),
            ("Cost of living", "mixed", "Santa Barbara's housing market is expensive; prospective students should factor local living costs into the value calculation."),
        ],
        [
            ("U.S. News — Best Undergraduate Computer Science", "https://www.usnews.com/best-colleges/rankings/computer-science-overall"),
            ("College Scorecard — UCSB Field of Study (Computer Science)", "https://collegescorecard.ed.gov/school/?110705"),
            ("UCSB Computer Science Department", "https://www.cs.ucsb.edu/"),
        ],
    ),
    "ucsb-economics-ba": _reviews(
        "UCSB Economics is a large, quantitatively rigorous department with a Nobel laureate and top field-level "
        "salary outcomes among UCSB majors; large class sizes are the main undergraduate caution.",
        [
            ("Quantitative rigor and recognition", "positive", "The department is home to Nobel laureate Finn Kydland and the Laboratory for Aggregate Economics and Finance, and is well regarded for macroeconomics and econometrics."),
            ("Strong salary outcomes", "positive", "College Scorecard reports a field-level median of about $59,500 one year after completion — among the highest of UCSB's non-engineering fields."),
            ("Accounting and finance pathways", "positive", "The related Economics & Accounting and Financial Mathematics & Statistics majors give students professional pathways into finance and accounting."),
            ("Large classes", "caution", "As one of UCSB's largest majors, introductory and core courses are large; students should seek out research and honors tracks for closer contact."),
        ],
        [
            ("College Scorecard — UCSB Field of Study (Economics)", "https://collegescorecard.ed.gov/school/?110705"),
            ("UCSB Department of Economics", "https://econ.ucsb.edu/"),
            ("U.S. News — UCSB undergraduate Economics standing", "https://www.usnews.com/best-colleges/university-of-california-santa-barbara-1320"),
        ],
    ),
    "ucsb-physics-phd": _reviews(
        "UCSB Physics is a top-ranked graduate program anchored by the Kavli Institute for Theoretical Physics "
        "and multiple Nobel laureates, with particular strength in condensed matter, quantum, and cosmology; "
        "selectivity is the realistic caution.",
        [
            ("Top-ranked, KITP-anchored", "positive", "U.S. News ranks UCSB physics #9 nationally; the department is home to the Kavli Institute for Theoretical Physics (KITP) and Nobel laureates including David Gross and the late Walter Kohn."),
            ("Condensed matter and quantum strength", "positive", "Reviewers highlight world-leading condensed-matter, quantum-materials, and cosmology research, with deep ties to the Materials department and Google's Santa Barbara quantum lab."),
            ("Funded doctorate", "positive", "Admitted PhD students receive tuition remission and a stipend."),
            ("Very selective", "caution", "A top-10 program with strong applicant demand — admission is highly competitive."),
        ],
        [
            ("U.S. News — Best Physics programs", "https://www.usnews.com/best-graduate-schools/top-science-schools/physics-rankings"),
            ("UCSB Department of Physics", "https://www.physics.ucsb.edu/"),
            ("Kavli Institute for Theoretical Physics", "https://www.kitp.ucsb.edu/"),
        ],
    ),
}


def _program_standard(spec: dict) -> dict:
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if "tracks" not in spec:
        omitted.append("tracks")
    omitted += ["class_profile.cohort_size", "faculty_contacts.lead"]
    if spec["degree_type"] == "bachelors":
        omitted.append("class_profile.test_scores (UC is test-free)")
    if spec["slug"] not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if not _has_tuition(spec):
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    return _standard(omitted)


# ── The program catalog (real UCSB degrees, resolved from the CIP list) ─────
def _p(slug, school, name, degree, dept, cip, desc, who, months=None, **kw):
    d = {
        "slug": slug, "school": school, "program_name": name, "field": kw.pop("field", name),
        "degree_type": degree, "department": dept, "cip": cip,
        "description": desc, "who": who,
        "duration_months": months if months is not None else {"bachelors": 48, "masters": 24, "phd": 60}.get(degree, 24),
    }
    d.update(kw)
    return d


PROGRAMS: list[dict] = [
    # ══════════ College of Letters and Science — Humanities & Fine Arts ══════════
    _p("ucsb-english-ba", _LS, "Bachelor of Arts in English", "bachelors", "Department of English", "23.01",
       "The study of literature in English across periods and media, combining close reading with literary theory, creative writing, and film and media options — one of UCSB's largest humanities majors.",
       "Students who love reading and writing and want a broad literary education with room to add creative writing, media, or a professional-writing minor.", field="English"),
    _p("ucsb-english-ma", _LS, "Master of Arts in English", "masters", "Department of English", "23.01",
       "Advanced literary study earned on the way to the doctorate, with department strengths in early-modern, Romantic, American, and literature-and-the-mind scholarship.",
       "Graduates deepening their literary-scholarship preparation en route to a PhD or a writing-intensive career.", field="English"),
    _p("ucsb-english-phd", _LS, "Doctor of Philosophy in English", "phd", "Department of English", "23.01",
       "A funded research doctorate training literary scholars, with notable strengths in early-modern studies, literature and the environment, and the literature-and-mind initiative.",
       "Aspiring literary scholars seeking a funded doctorate with strong faculty mentorship and a distinctive literature-and-mind focus.", field="English"),
    _p("ucsb-comparative-literature-ba", _LS, "Bachelor of Arts in Comparative Literature", "bachelors", "Comparative Literature Program", "16.01",
       "Reading literature across languages, national traditions, and media through the lens of critical theory, with a language requirement that supports study abroad and double majors.",
       "Students who want to read literature across languages and cultures and engage seriously with literary and critical theory.", field="Comparative Literature"),
    _p("ucsb-comparative-literature-phd", _LS, "Doctor of Philosophy in Comparative Literature", "phd", "Comparative Literature Program", "16.01",
       "A cross-linguistic doctoral program relating literature, theory, and translation across traditions, drawing faculty from UCSB's many language and literature departments.",
       "Aspiring scholars who work across languages and want an interdisciplinary doctorate grounded in critical theory.", field="Comparative Literature"),
    _p("ucsb-linguistics-ba", _LS, "Bachelor of Arts in Linguistics", "bachelors", "Department of Linguistics", "16.01",
       "The scientific study of language — phonetics, phonology, syntax, semantics, and how language is used in interaction — with UCSB strengths in usage-based and functional approaches.",
       "Students fascinated by how language is structured and used who want a rigorous science-of-language major.", field="Linguistics"),
    _p("ucsb-linguistics-ma", _LS, "Master of Arts in Linguistics", "masters", "Department of Linguistics", "16.01",
       "Graduate training in linguistic theory and analysis earned toward the doctorate, with department strengths in interactional linguistics and language documentation.",
       "Graduates advancing toward doctoral work or language-related careers who want grounding in usage-based linguistics.", field="Linguistics"),
    _p("ucsb-linguistics-phd", _LS, "Doctor of Philosophy in Linguistics", "phd", "Department of Linguistics", "16.01",
       "A funded doctorate known for usage-based, functional, and interactional approaches to grammar and for language documentation of understudied languages.",
       "Aspiring linguists drawn to usage-based theory, discourse, and the documentation of endangered languages.", field="Linguistics"),
    _p("ucsb-language-culture-society-ba", _LS, "Bachelor of Arts in Language, Culture, and Society", "bachelors", "Department of Linguistics", "16.01",
       "An interdisciplinary major examining how language shapes identity, power, and social life, bridging linguistics with anthropology and communication.",
       "Students interested in language as a social force — identity, multilingualism, and communication across communities.", field="Language, Culture, and Society"),
    _p("ucsb-philosophy-ba", _LS, "Bachelor of Arts in Philosophy", "bachelors", "Department of Philosophy", "38.01",
       "Rigorous training in logic, ethics, metaphysics, epistemology, and the history of philosophy, with UCSB strengths in philosophy of mind and the mind-body problem.",
       "Students who want disciplined training in argument, ethics, and reasoning, including strong preparation for law and analytic careers.", field="Philosophy"),
    _p("ucsb-philosophy-phd", _LS, "Doctor of Philosophy in Philosophy", "phd", "Department of Philosophy", "38.01",
       "A funded doctoral program with recognized strengths in philosophy of mind, metaphysics, and the philosophy of science, training scholars for research and teaching.",
       "Aspiring philosophers seeking a doctorate with particular strength in mind, metaphysics, and philosophy of science.", field="Philosophy"),
    _p("ucsb-religious-studies-ba", _LS, "Bachelor of Arts in Religious Studies", "bachelors", "Department of Religious Studies", "38.02",
       "The comparative, historical study of religious texts, traditions, and practices across the world's cultures, one of the largest and most highly regarded religious-studies departments in the country.",
       "Students curious how religion shapes history, culture, politics, and ethics, and who want a text- and culture-based humanities major.", field="Religious Studies"),
    _p("ucsb-religious-studies-ma", _LS, "Master of Arts in Religious Studies", "masters", "Department of Religious Studies", "38.02",
       "Advanced study of religious traditions and methods for the study of religion, earned toward doctoral work in a nationally regarded department.",
       "Graduates deepening their study of religion before a PhD or a career in education, publishing, or the nonprofit sector.", field="Religious Studies"),
    _p("ucsb-religious-studies-phd", _LS, "Doctor of Philosophy in Religious Studies", "phd", "Department of Religious Studies", "38.02",
       "A funded doctorate spanning the world's religious traditions and the theory and method of the field, in one of the country's leading religious-studies departments.",
       "Aspiring scholars of religion seeking a broad, methodologically rigorous doctorate across traditions.", field="Religious Studies"),
    _p("ucsb-classics-ba", _LS, "Bachelor of Arts in Classics", "bachelors", "Department of Classics", "16.12",
       "The languages, literature, history, and archaeology of ancient Greece and Rome, with tracks for reading Greek and Latin in the original and for classical civilization in translation.",
       "Students drawn to the ancient Mediterranean who want to read Greek and Latin or study classical civilization broadly.", field="Classics"),
    _p("ucsb-classics-phd", _LS, "Doctor of Philosophy in Classics", "phd", "Department of Classics", "16.12",
       "A funded doctorate in Greek and Latin literature, ancient history, and classical scholarship, training researchers and teachers of the ancient world.",
       "Aspiring classicists who want doctoral training in the languages, literature, and history of Greece and Rome.", field="Classics"),
    _p("ucsb-french-ba", _LS, "Bachelor of Arts in French", "bachelors", "Department of French and Italian", "16.09",
       "French language and the literatures and cultures of France and the wider Francophone world, from medieval texts to contemporary film and cultural theory.",
       "Students who want French fluency alongside deep engagement with French and Francophone literature and culture.", field="French"),
    _p("ucsb-italian-studies-ba", _LS, "Bachelor of Arts in Italian Studies", "bachelors", "Department of French and Italian", "16.09",
       "Italian language and culture from Dante and the Renaissance to modern Italian literature, cinema, and society, with study-abroad pathways to Italy.",
       "Students drawn to Italian language, art, and literature and the culture of Italy.", field="Italian Studies"),
    _p("ucsb-spanish-ba", _LS, "Bachelor of Arts in Spanish", "bachelors", "Department of Spanish and Portuguese", "16.09",
       "Advanced Spanish paired with the study of the literatures and cultures of Spain, Latin America, and U.S. Latino communities, going well beyond language proficiency.",
       "Students who want fluency in Spanish and serious study of Hispanic literatures and cultures.", field="Spanish"),
    _p("ucsb-portuguese-ba", _LS, "Bachelor of Arts in Portuguese", "bachelors", "Department of Spanish and Portuguese", "16.09",
       "Portuguese language and the literatures and cultures of Brazil, Portugal, and Lusophone Africa, complementing Latin American and Iberian study at UCSB.",
       "Students who want Portuguese proficiency and access to Brazilian and Lusophone literature and culture.", field="Portuguese"),
    _p("ucsb-hispanic-languages-phd", _LS, "Doctor of Philosophy in Hispanic Languages and Literatures", "phd", "Department of Spanish and Portuguese", "16.09",
       "A funded doctorate in Peninsular, Latin American, and Luso-Brazilian literatures and cultures, training scholars of the Hispanic and Lusophone worlds.",
       "Aspiring scholars of Spanish, Latin American, and Lusophone literatures seeking a research doctorate.", field="Hispanic Languages and Literatures"),
    _p("ucsb-german-ba", _LS, "Bachelor of Arts in German", "bachelors", "Department of Germanic and Slavic Studies", "16.05",
       "German language, literature, and thought, from the classics of German philosophy and literature to contemporary German-speaking culture, media, and film.",
       "Students who want German fluency and access to the German intellectual, literary, and film tradition.", field="German"),
    _p("ucsb-germanic-slavic-phd", _LS, "Doctor of Philosophy in Germanic and Slavic Studies", "phd", "Department of Germanic and Slavic Studies", "16.05",
       "A funded doctorate in German and Slavic literatures, cultures, and thought, spanning literary history, media, and critical theory.",
       "Aspiring scholars of German or Slavic literature and culture seeking a research doctorate.", field="Germanic and Slavic Studies"),
    _p("ucsb-chinese-ba", _LS, "Bachelor of Arts in Chinese", "bachelors", "Department of East Asian Languages and Cultural Studies", "16.03",
       "Chinese language across all levels combined with the study of Chinese literature, film, and culture within a strong East Asian studies department.",
       "Students who want Chinese proficiency and engagement with Chinese literature, media, and culture.", field="Chinese"),
    _p("ucsb-japanese-ba", _LS, "Bachelor of Arts in Japanese", "bachelors", "Department of East Asian Languages and Cultural Studies", "16.03",
       "Japanese language paired with the study of Japanese literature, film, and popular culture, complementing UCSB's East Asian studies offerings.",
       "Students who want Japanese proficiency and access to Japanese literature, media, and culture.", field="Japanese"),
    _p("ucsb-east-asian-studies-ba", _LS, "Bachelor of Arts in East Asian Studies", "bachelors", "Department of East Asian Languages and Cultural Studies", "05.01",
       "An interdisciplinary major on the histories, cultures, and societies of China, Japan, and Korea, combining language study with literature, history, and religion.",
       "Students interested in East Asia who want to combine language with the region's history, culture, and society.", field="East Asian Studies"),
    _p("ucsb-east-asian-cultural-studies-phd", _LS, "Doctor of Philosophy in East Asian Languages and Cultural Studies", "phd", "Department of East Asian Languages and Cultural Studies", "16.03",
       "A funded doctorate in the literatures, cultures, and intellectual traditions of China, Japan, and Korea, from premodern texts to contemporary media.",
       "Aspiring scholars of East Asian literature and culture seeking a research doctorate.", field="East Asian Languages and Cultural Studies"),
    _p("ucsb-history-ba", _LS, "Bachelor of Arts in History", "bachelors", "Department of History", "54.01",
       "The study of the human past across regions and eras, training students to analyze primary sources and construct evidence-based historical arguments.",
       "Students who want to understand how the past shaped the present and to build strong research and writing skills.", field="History"),
    _p("ucsb-history-public-policy-ba", _LS, "Bachelor of Arts in History of Public Policy, Law, and Governance", "bachelors", "Department of History", "54.01",
       "A History-department major examining how law, policy, and institutions of governance have developed over time — designed with pre-law and public-service pathways in mind.",
       "Students interested in law, government, and public policy who want a historical foundation and pre-law preparation.", field="History of Public Policy, Law, and Governance"),
    _p("ucsb-history-ma", _LS, "Master of Arts in History", "masters", "Department of History", "54.01",
       "Advanced historical research and methods earned toward the doctorate, with department strengths in the history of science, environment, and the Americas.",
       "Graduates deepening their historical research before a PhD or a career in education, archives, or public history.", field="History"),
    _p("ucsb-history-phd", _LS, "Doctor of Philosophy in History", "phd", "Department of History", "54.01",
       "A funded doctorate with recognized strengths in the history of science and technology, environmental history, and the history of the Americas.",
       "Aspiring historians seeking a research doctorate with strengths in science, environment, and the Americas.", field="History"),
    _p("ucsb-history-art-architecture-ba", _LS, "Bachelor of Arts in History of Art and Architecture", "bachelors", "Department of the History of Art and Architecture", "50.07",
       "The history of art, architecture, and visual culture across periods and world traditions, developing skills in visual analysis and cultural interpretation.",
       "Students who want to study art and the built environment and pursue museum, gallery, or graduate pathways.", field="History of Art and Architecture"),
    _p("ucsb-history-art-architecture-ma", _LS, "Master of Arts in History of Art and Architecture", "masters", "Department of the History of Art and Architecture", "50.07",
       "Advanced study of art and architectural history and theory earned toward the doctorate, spanning global periods and media.",
       "Graduates advancing toward doctoral study or museum and curatorial careers in art and architectural history.", field="History of Art and Architecture"),
    _p("ucsb-history-art-architecture-phd", _LS, "Doctor of Philosophy in History of Art and Architecture", "phd", "Department of the History of Art and Architecture", "50.07",
       "A funded doctorate in the history and theory of art and architecture, from antiquity to the contemporary, across global traditions.",
       "Aspiring art and architectural historians seeking a research doctorate with global breadth.", field="History of Art and Architecture"),
    _p("ucsb-art-ba", _LS, "Bachelor of Arts in Art", "bachelors", "Department of Art", "50.07",
       "Studio practice across drawing, painting, sculpture, photography, and new media, with critique-based training that culminates in independent creative projects.",
       "Students who want to make art in a research-university setting with strong ties to new media and technology.", field="Art"),
    _p("ucsb-art-mfa", _LS, "Master of Fine Arts in Art", "masters", "Department of Art", "50.07",
       "A studio-intensive terminal degree developing an independent contemporary-art practice through critique, seminars, and a thesis exhibition, with strengths in new media.",
       "Practicing artists seeking a terminal studio degree with strong new-media and interdisciplinary options.", field="Art", months=36),
    _p("ucsb-music-ba", _LS, "Bachelor of Arts in Music", "bachelors", "Department of Music", "50.09",
       "The study of music — theory, history, and musicianship — with performance opportunities across ensembles, for students pursuing music broadly within a liberal-arts framework.",
       "Students who want to study music history, theory, and performance within a broad liberal-arts degree.", field="Music"),
    _p("ucsb-music-performance-bm", _LS, "Bachelor of Music in Performance", "bachelors", "Department of Music", "50.09",
       "A performance-focused degree combining applied lessons, ensembles, and recitals with music theory and history for students committed to a performing path.",
       "Students committed to instrumental or vocal performance who want conservatory-style training within a research university.", field="Music Performance"),
    _p("ucsb-music-ma", _LS, "Master of Arts in Music", "masters", "Department of Music", "50.09",
       "Graduate study in musicology, music theory, composition, or ethnomusicology earned toward the doctorate, drawing on UCSB's research collections and computing.",
       "Graduates advancing in musicology, theory, composition, or ethnomusicology toward doctoral work.", field="Music"),
    _p("ucsb-music-phd", _LS, "Doctor of Philosophy in Music", "phd", "Department of Music", "50.09",
       "A funded doctorate in musicology, music theory, and ethnomusicology, with strengths in music and technology and the study of global musical traditions.",
       "Aspiring music scholars seeking a research doctorate spanning musicology, theory, and ethnomusicology.", field="Music"),
    _p("ucsb-theater-ba", _LS, "Bachelor of Arts in Theater", "bachelors", "Department of Theater and Dance", "50.05",
       "The study and practice of theater — acting, directing, design, and dramatic literature — combining performance training with critical and historical study.",
       "Students who want to study and make theater, from performance and design to dramaturgy and theater history.", field="Theater"),
    _p("ucsb-theater-phd", _LS, "Doctor of Philosophy in Theater and Performance Studies", "phd", "Department of Theater and Dance", "50.05",
       "A funded doctorate in theater and performance studies, analyzing performance across cultures and its social and political dimensions.",
       "Aspiring scholars of theater and performance seeking a research doctorate.", field="Theater and Performance Studies"),
    _p("ucsb-dance-ba", _LS, "Bachelor of Arts in Dance", "bachelors", "Department of Theater and Dance", "50.03",
       "Technical training across modern, ballet, and world-dance forms combined with choreography, dance history, and performance in a strong dance program.",
       "Students who want rigorous dance training and choreographic practice within a research university.", field="Dance"),
    _p("ucsb-film-media-studies-ba", _LS, "Bachelor of Arts in Film and Media Studies", "bachelors", "Department of Film and Media Studies", "50.06",
       "The critical study of film, television, and digital media — history, theory, and analysis — alongside foundational production, in a nationally recognized department.",
       "Students who want to analyze and understand film, television, and digital media, with some hands-on production.", field="Film and Media Studies"),
    _p("ucsb-film-media-studies-phd", _LS, "Doctor of Philosophy in Film and Media Studies", "phd", "Department of Film and Media Studies", "50.06",
       "A funded doctorate in the history and theory of film and media, examining moving-image culture from early cinema to networked digital media.",
       "Aspiring film and media scholars seeking a research doctorate in moving-image and digital-media culture.", field="Film and Media Studies"),
    _p("ucsb-medieval-studies-ba", _LS, "Bachelor of Arts in Medieval Studies", "bachelors", "Medieval Studies Program", "30.13",
       "An interdisciplinary major on the European and Mediterranean Middle Ages, integrating history, literature, art, religion, and language study.",
       "Students fascinated by the medieval world who want an interdisciplinary humanities major across history, literature, and art.", field="Medieval Studies"),

    # ══════════ College of Letters and Science — Interdisciplinary & Area / Ethnic Studies ══════════
    _p("ucsb-global-studies-ba", _LS, "Bachelor of Arts in Global Studies", "bachelors", "Department of Global Studies", "30.20",
       "The interdisciplinary study of globalization — its political, economic, cultural, and environmental dimensions — with a language requirement and study-abroad pathways.",
       "Students interested in globalization, international affairs, and cross-cultural work who want an interdisciplinary social-science major.", field="Global Studies"),
    _p("ucsb-global-studies-ma", _LS, "Master of Arts in Global Studies", "masters", "Department of Global Studies", "30.20",
       "Advanced interdisciplinary study of global political economy, culture, and governance, earned toward the doctorate in a leading global-studies program.",
       "Graduates advancing in global and international studies toward doctoral work or international careers.", field="Global Studies"),
    _p("ucsb-global-studies-phd", _LS, "Doctor of Philosophy in Global Studies", "phd", "Department of Global Studies", "30.20",
       "A funded doctorate examining globalization across politics, economy, culture, and environment, one of the field's pioneering doctoral programs.",
       "Aspiring scholars of globalization and transnational affairs seeking an interdisciplinary research doctorate.", field="Global Studies"),
    _p("ucsb-latin-american-iberian-ba", _LS, "Bachelor of Arts in Latin American and Iberian Studies", "bachelors", "Latin American and Iberian Studies Program", "05.01",
       "An interdisciplinary major on the histories, cultures, politics, and languages of Latin America and the Iberian Peninsula.",
       "Students drawn to Latin America and Iberia who want an interdisciplinary major spanning history, culture, and politics.", field="Latin American and Iberian Studies"),
    _p("ucsb-latin-american-iberian-ma", _LS, "Master of Arts in Latin American and Iberian Studies", "masters", "Latin American and Iberian Studies Program", "05.01",
       "Interdisciplinary graduate study of Latin America and Iberia across the humanities and social sciences, with language and area-studies depth.",
       "Graduates seeking interdisciplinary regional expertise for doctoral work, government, or international careers.", field="Latin American and Iberian Studies"),
    _p("ucsb-middle-east-studies-ba", _LS, "Bachelor of Arts in Middle East Studies", "bachelors", "Middle East Studies Program", "05.01",
       "An interdisciplinary major on the languages, histories, religions, and politics of the Middle East and North Africa.",
       "Students interested in the Middle East who want an interdisciplinary major combining language with history, religion, and politics.", field="Middle East Studies"),
    _p("ucsb-russian-east-european-ba", _LS, "Bachelor of Arts in Russian and East European Studies", "bachelors", "Russian and East European Studies Program", "05.01",
       "An interdisciplinary major on the languages, literatures, histories, and politics of Russia and Eastern Europe.",
       "Students drawn to Russia and Eastern Europe who want an interdisciplinary major combining language, literature, and area study.", field="Russian and East European Studies"),
    _p("ucsb-asian-american-studies-ba", _LS, "Bachelor of Arts in Asian American Studies", "bachelors", "Department of Asian American Studies", "05.02",
       "The interdisciplinary study of the histories, cultures, and communities of Asian Americans and Pacific Islanders, in one of the country's few dedicated departments.",
       "Students interested in Asian American and Pacific Islander history, culture, and social justice.", field="Asian American Studies"),
    _p("ucsb-black-studies-ba", _LS, "Bachelor of Arts in Black Studies", "bachelors", "Department of Black Studies", "05.02",
       "The interdisciplinary study of the history, culture, politics, and creative expression of Black people across Africa and the diaspora.",
       "Students who want to study the history, culture, and politics of the African diaspora across disciplines.", field="Black Studies"),
    _p("ucsb-chicana-chicano-studies-ba", _LS, "Bachelor of Arts in Chicana and Chicano Studies", "bachelors", "Department of Chicana and Chicano Studies", "05.02",
       "The interdisciplinary study of the history, culture, politics, and experience of Chicana/o and Latina/o communities in the United States.",
       "Students interested in Chicana/o and Latina/o history, culture, and social justice across disciplines.", field="Chicana and Chicano Studies"),
    _p("ucsb-chicana-chicano-studies-phd", _LS, "Doctor of Philosophy in Chicana and Chicano Studies", "phd", "Department of Chicana and Chicano Studies", "05.02",
       "A funded doctorate — among the first of its kind — advancing interdisciplinary research on Chicana/o and Latina/o histories, cultures, and politics.",
       "Aspiring scholars of Chicana/o and Latina/o studies seeking a pioneering interdisciplinary doctorate.", field="Chicana and Chicano Studies"),
    _p("ucsb-feminist-studies-ba", _LS, "Bachelor of Arts in Feminist Studies", "bachelors", "Department of Feminist Studies", "05.02",
       "The interdisciplinary study of gender, sexuality, and power across cultures and institutions, combining feminist theory with social and cultural analysis.",
       "Students interested in gender and sexuality studies who want an interdisciplinary, theory-informed major.", field="Feminist Studies"),
    _p("ucsb-feminist-studies-phd", _LS, "Doctor of Philosophy in Feminist Studies", "phd", "Department of Feminist Studies", "05.02",
       "A funded doctorate in feminist theory and the transnational study of gender, sexuality, and power across disciplines.",
       "Aspiring scholars of gender and sexuality seeking an interdisciplinary feminist-studies doctorate.", field="Feminist Studies"),
    _p("ucsb-asian-studies-ma", _LS, "Master of Arts in Asian Studies", "masters", "Interdisciplinary Asian Studies Program", "05.01",
       "An interdisciplinary graduate degree on the cultures, histories, and societies of Asia, drawing faculty from across the humanities and social sciences.",
       "Graduates seeking interdisciplinary regional expertise in Asia for doctoral work or international careers.", field="Asian Studies"),

    # ══════════ College of Letters and Science — Social Sciences ══════════
    _p("ucsb-anthropology-ba", _LS, "Bachelor of Arts in Anthropology", "bachelors", "Department of Anthropology", "45.02",
       "The four-field study of humanity — sociocultural, biological, archaeological, and linguistic anthropology — with UCSB strengths in evolutionary and integrative anthropology.",
       "Students curious about human societies, evolution, and cultures who want a four-field anthropological education.", field="Anthropology"),
    _p("ucsb-anthropology-ma", _LS, "Master of Arts in Anthropology", "masters", "Department of Anthropology", "45.02",
       "Advanced anthropological training earned toward the doctorate, with department strengths in evolutionary anthropology and integrative approaches.",
       "Graduates advancing toward doctoral research in sociocultural, biological, or archaeological anthropology.", field="Anthropology"),
    _p("ucsb-anthropology-phd", _LS, "Doctor of Philosophy in Anthropology", "phd", "Department of Anthropology", "45.02",
       "A funded doctorate spanning sociocultural, biological, and archaeological anthropology, nationally known for evolutionary and integrative research.",
       "Aspiring anthropologists seeking a research doctorate with strength in evolutionary and integrative anthropology.", field="Anthropology"),
    _p("ucsb-communication-ba", _LS, "Bachelor of Arts in Communication", "bachelors", "Department of Communication", "09.01",
       "The social-scientific study of human communication — interpersonal, media, and organizational — grounded in theory and empirical research methods.",
       "Students interested in how communication and media shape behavior, relationships, and society, with a research-methods foundation.", field="Communication"),
    _p("ucsb-communication-ma", _LS, "Master of Arts in Communication", "masters", "Department of Communication", "09.01",
       "Advanced study of communication theory and research methods earned toward the doctorate in a top-ranked social-science communication department.",
       "Graduates advancing toward doctoral work in the social science of communication and media effects.", field="Communication"),
    _p("ucsb-communication-phd", _LS, "Doctor of Philosophy in Communication", "phd", "Department of Communication", "09.01",
       "A funded doctorate — among the nation's top communication programs — advancing rigorous social-scientific research on media, technology, and interaction.",
       "Aspiring communication scientists seeking a top-ranked research doctorate in media and interpersonal communication.", field="Communication"),
    _p("ucsb-economics-ba", _LS, "Bachelor of Arts in Economics", "bachelors", "Department of Economics", "45.06",
       "The analysis of how individuals, firms, and governments allocate resources, combining microeconomics, macroeconomics, and econometrics with strong quantitative training.",
       "Students who want rigorous, quantitative training in economics for careers in business, policy, finance, or graduate study.", field="Economics"),
    _p("ucsb-economics-accounting-ba", _LS, "Bachelor of Arts in Economics and Accounting", "bachelors", "Department of Economics", "52.06",
       "An economics major with an accounting concentration meeting professional accounting course requirements, pairing economic analysis with financial and managerial accounting.",
       "Students headed for accounting, finance, or CPA pathways who want an economics core with accounting depth.", field="Economics and Accounting"),
    _p("ucsb-economics-phd", _LS, "Doctor of Philosophy in Economics", "phd", "Department of Economics", "45.06",
       "A funded doctorate with recognized strengths in macroeconomics, econometrics, and finance, home to a Nobel laureate and the Laboratory for Aggregate Economics and Finance.",
       "Aspiring economists seeking a research doctorate with strength in macroeconomics, econometrics, and finance.", field="Economics"),
    _p("ucsb-political-science-ba", _LS, "Bachelor of Arts in Political Science", "bachelors", "Department of Political Science", "45.10",
       "The study of government, politics, and public policy across American politics, comparative politics, international relations, and political theory.",
       "Students interested in government, elections, policy, and international affairs, including pre-law preparation.", field="Political Science"),
    _p("ucsb-political-science-ma", _LS, "Master of Arts in Political Science", "masters", "Department of Political Science", "45.10",
       "Advanced study of political behavior, institutions, and international relations with quantitative methods, earned toward the doctorate.",
       "Graduates advancing toward doctoral research in political science and quantitative political analysis.", field="Political Science"),
    _p("ucsb-political-science-phd", _LS, "Doctor of Philosophy in Political Science", "phd", "Department of Political Science", "45.10",
       "A funded doctorate with strengths in political behavior, international relations, and formal and quantitative methods.",
       "Aspiring political scientists seeking a research doctorate with strong methodological training.", field="Political Science"),
    _p("ucsb-sociology-ba", _LS, "Bachelor of Arts in Sociology", "bachelors", "Department of Sociology", "45.11",
       "The study of social structures, inequality, institutions, and change, combining sociological theory with quantitative and qualitative research methods.",
       "Students interested in inequality, institutions, and social change who want research training for policy, law, or social work.", field="Sociology"),
    _p("ucsb-sociology-phd", _LS, "Doctor of Philosophy in Sociology", "phd", "Department of Sociology", "45.11",
       "A funded doctorate with strengths in gender, race, culture, and social psychology, training researchers and teachers of sociology.",
       "Aspiring sociologists seeking a research doctorate with strengths in inequality, culture, and social psychology.", field="Sociology"),
    _p("ucsb-geography-ba", _LS, "Bachelor of Arts in Geography", "bachelors", "Department of Geography", "45.07",
       "The study of the earth's physical and human systems and the geographic technologies — GIS, remote sensing, and spatial analysis — used to understand them.",
       "Students interested in the environment, cities, and spatial data who want training in GIS and geographic analysis.", field="Geography"),
    _p("ucsb-geography-ma", _LS, "Master of Arts in Geography", "masters", "Department of Geography", "45.07",
       "Advanced study of physical or human geography and geographic information science, earned toward the doctorate in a top-ranked department.",
       "Graduates advancing toward doctoral work in geography or geographic information science.", field="Geography"),
    _p("ucsb-geography-phd", _LS, "Doctor of Philosophy in Geography", "phd", "Department of Geography", "45.07",
       "A funded doctorate — a national leader in geographic information science — spanning physical, human, and computational geography.",
       "Aspiring geographers seeking a top-ranked doctorate, especially in geographic information science and spatial analysis.", field="Geography"),
    _p("ucsb-psychological-brain-sciences-bs", _LS, "Bachelor of Science in Psychological and Brain Sciences", "bachelors", "Department of Psychological and Brain Sciences", "42.01",
       "The scientific study of mind, brain, and behavior — from cognition and neuroscience to social and developmental psychology — with strong research-methods training.",
       "Students who want a research-oriented, science-based psychology degree spanning cognition, neuroscience, and behavior.", field="Psychological and Brain Sciences"),
    _p("ucsb-biopsychology-bs", _LS, "Bachelor of Science in Biopsychology", "bachelors", "Department of Psychological and Brain Sciences", "42.27",
       "The biological bases of behavior — neuroscience, hormones, and brain systems — for students bridging psychology and the life sciences.",
       "Students fascinated by the brain and behavior who want a neuroscience-leaning psychology major.", field="Biopsychology"),
    _p("ucsb-psychological-brain-sciences-phd", _LS, "Doctor of Philosophy in Psychological and Brain Sciences", "phd", "Department of Psychological and Brain Sciences", "42.01",
       "A funded doctorate spanning cognition and perception, neuroscience and behavior, developmental, and social psychology, tied to the Neuroscience Research Institute.",
       "Aspiring psychological and brain scientists seeking a research doctorate across cognition, neuroscience, and behavior.", field="Psychological and Brain Sciences"),

    # ══════════ College of Letters and Science — Mathematical & Physical Sciences ══════════
    _p("ucsb-mathematics-bs", _LS, "Bachelor of Science in Mathematics", "bachelors", "Department of Mathematics", "27.01",
       "Rigorous training in pure and applied mathematics — analysis, algebra, and geometry — with pathways toward graduate study, teaching, or quantitative careers.",
       "Students who love mathematical reasoning and want a strong foundation for graduate study or quantitative work.", field="Mathematics"),
    _p("ucsb-applied-mathematics-bs", _LS, "Bachelor of Science in Applied Mathematics", "bachelors", "Department of Mathematics", "27.03",
       "Mathematics applied to science, engineering, and data — differential equations, modeling, numerical methods, and optimization — for problem-solving careers.",
       "Students who want to use mathematics to model and solve real-world problems in science, engineering, and data.", field="Applied Mathematics"),
    _p("ucsb-mathematics-ma", _LS, "Master of Arts in Mathematics", "masters", "Department of Mathematics", "27.01",
       "Advanced coursework in pure or applied mathematics earned toward the doctorate or a quantitative career, with an optional computational science emphasis.",
       "Graduates advancing in mathematics toward doctoral study or quantitative and computational careers.", field="Mathematics"),
    _p("ucsb-mathematics-phd", _LS, "Doctor of Philosophy in Mathematics", "phd", "Department of Mathematics", "27.01",
       "A funded doctorate spanning pure and applied mathematics, with strengths in geometry, topology, analysis, and mathematical physics.",
       "Aspiring mathematicians seeking a research doctorate across pure and applied mathematics.", field="Mathematics"),
    _p("ucsb-statistics-data-science-bs", _LS, "Bachelor of Science in Statistics and Data Science", "bachelors", "Department of Statistics and Applied Probability", "27.05",
       "The theory and practice of statistics and data science — probability, statistical inference, machine learning, and data analysis — with strong computing.",
       "Students who want to turn data into insight and are headed for analytics, data science, or quantitative careers.", field="Statistics and Data Science"),
    _p("ucsb-actuarial-science-bs", _LS, "Bachelor of Science in Actuarial Science", "bachelors", "Department of Statistics and Applied Probability", "52.13",
       "The mathematics of risk — probability, financial mathematics, and statistics aligned with professional actuarial exams — for careers in insurance and finance.",
       "Students headed for the actuarial profession who want exam-aligned training in probability, finance, and statistics.", field="Actuarial Science"),
    _p("ucsb-financial-math-statistics-bs", _LS, "Bachelor of Science in Financial Mathematics and Statistics", "bachelors", "Department of Statistics and Applied Probability", "27.05",
       "A quantitative major combining statistics, probability, and financial mathematics with economics, aimed at quantitative finance and analytics careers.",
       "Students headed for quantitative finance or analytics who want a statistics-and-finance core.", field="Financial Mathematics and Statistics"),
    _p("ucsb-statistics-ma", _LS, "Master of Arts in Statistics", "masters", "Department of Statistics and Applied Probability", "27.05",
       "Advanced statistics and data science — inference, computation, and applied probability — earned toward the doctorate or analytics careers.",
       "Graduates advancing in statistics and data science toward doctoral study or quantitative careers.", field="Statistics"),
    _p("ucsb-statistics-phd", _LS, "Doctor of Philosophy in Statistics and Applied Probability", "phd", "Department of Statistics and Applied Probability", "27.05",
       "A funded doctorate in statistics and applied probability, with strengths in probability theory, statistical machine learning, and financial mathematics.",
       "Aspiring statisticians and probabilists seeking a research doctorate in statistics and applied probability.", field="Statistics and Applied Probability"),
    _p("ucsb-physics-bs", _LS, "Bachelor of Science in Physics", "bachelors", "Department of Physics", "40.08",
       "The fundamental study of matter, energy, and the universe — mechanics, electromagnetism, quantum mechanics, and thermodynamics — with strong research options.",
       "Students who want to understand the physical universe and pursue physics research, engineering, or quantitative careers.", field="Physics"),
    _p("ucsb-physics-phd", _LS, "Doctor of Philosophy in Physics", "phd", "Department of Physics", "40.08",
       "A top-10, funded doctorate anchored by the Kavli Institute for Theoretical Physics and multiple Nobel laureates, with strengths in condensed matter, quantum, and cosmology.",
       "Aspiring physicists seeking a top-ranked research doctorate, especially in condensed matter, quantum science, and cosmology.", field="Physics"),
    _p("ucsb-chemistry-bs", _LS, "Bachelor of Science in Chemistry", "bachelors", "Department of Chemistry and Biochemistry", "40.05",
       "The study of matter and its transformations — organic, inorganic, physical, and analytical chemistry — with extensive laboratory and undergraduate-research work.",
       "Students who want a rigorous, lab-intensive chemistry degree with strong research and pre-health options.", field="Chemistry"),
    _p("ucsb-biochemistry-bs", _LS, "Bachelor of Science in Biochemistry", "bachelors", "Department of Chemistry and Biochemistry", "26.02",
       "The chemistry of living systems — proteins, nucleic acids, metabolism, and molecular structure — bridging chemistry and the life sciences.",
       "Students at the interface of chemistry and biology, including pre-health and molecular-research pathways.", field="Biochemistry"),
    _p("ucsb-chemistry-phd", _LS, "Doctor of Philosophy in Chemistry", "phd", "Department of Chemistry and Biochemistry", "40.05",
       "A funded doctorate across organic, inorganic, physical, and biological chemistry, home to a Nobel laureate and strong materials-chemistry ties.",
       "Aspiring chemists seeking a research doctorate with strengths spanning materials, physical, and biological chemistry.", field="Chemistry"),
    _p("ucsb-earth-science-bs", _LS, "Bachelor of Science in Earth Science", "bachelors", "Department of Earth Science", "40.06",
       "The study of the Earth — its materials, processes, and history — spanning geology, geophysics, and environmental and climate science, with strong field work.",
       "Students interested in the Earth, climate, and natural hazards who want field- and lab-based science.", field="Earth Science"),
    _p("ucsb-earth-science-ms", _LS, "Master of Science in Earth Science", "masters", "Department of Earth Science", "40.06",
       "Advanced study in geology, geophysics, or environmental earth science earned toward the doctorate or applied geoscience careers.",
       "Graduates advancing in the geosciences toward doctoral study or applied earth-science careers.", field="Earth Science"),
    _p("ucsb-earth-science-phd", _LS, "Doctor of Philosophy in Earth Science", "phd", "Department of Earth Science", "40.06",
       "A funded doctorate spanning geology, geophysics, geochemistry, and climate and tectonics, with strong ties to marine and environmental science.",
       "Aspiring earth scientists seeking a research doctorate across geology, geophysics, and climate science.", field="Earth Science"),

    # ══════════ College of Letters and Science — Biological & Marine Sciences ══════════
    _p("ucsb-biological-sciences-bs", _LS, "Bachelor of Science in Biological Sciences", "bachelors", "Department of Molecular, Cellular, and Developmental Biology", "26.01",
       "A broad life-sciences major spanning molecular and cellular biology, genetics, physiology, and ecology, with emphases and strong pre-health and research pathways.",
       "Students who want a broad life-sciences foundation with pre-health, research, or specialized-biology options.", field="Biological Sciences"),
    _p("ucsb-molecular-cellular-biology-bs", _LS, "Bachelor of Science in Molecular and Cellular Biology", "bachelors", "Department of Molecular, Cellular, and Developmental Biology", "26.04",
       "The study of life at the molecular and cellular level — genetics, biochemistry, cell signaling, and development — with heavy laboratory training.",
       "Students focused on the molecular machinery of life, including biotech, research, and pre-health pathways.", field="Molecular and Cellular Biology"),
    _p("ucsb-physiology-bs", _LS, "Bachelor of Science in Physiology", "bachelors", "Department of Molecular, Cellular, and Developmental Biology", "26.09",
       "The study of how living systems function — from cells and organs to whole-body physiology — with strong preparation for the health professions.",
       "Students drawn to how the body works, including strong preparation for medicine and other health careers.", field="Physiology"),
    _p("ucsb-mcdb-phd", _LS, "Doctor of Philosophy in Molecular, Cellular, and Developmental Biology", "phd", "Department of Molecular, Cellular, and Developmental Biology", "26.04",
       "A funded doctorate in molecular, cellular, and developmental biology, with strengths in cell signaling, development, neurobiology, and plant biology.",
       "Aspiring molecular and cell biologists seeking a funded research doctorate.", field="Molecular, Cellular, and Developmental Biology"),
    _p("ucsb-ecology-evolution-bs", _LS, "Bachelor of Science in Ecology and Evolution", "bachelors", "Department of Ecology, Evolution, and Marine Biology", "26.13",
       "The study of organisms, populations, and ecosystems and the evolutionary processes that shape them, with field opportunities at UCSB's coastal reserves.",
       "Students fascinated by ecosystems, biodiversity, and evolution who want field- and research-based biology.", field="Ecology and Evolution"),
    _p("ucsb-aquatic-biology-bs", _LS, "Bachelor of Science in Aquatic Biology", "bachelors", "Department of Ecology, Evolution, and Marine Biology", "26.13",
       "The biology of marine and freshwater life and ecosystems, drawing on UCSB's oceanfront setting, the campus Lagoon, and the Marine Science Institute.",
       "Students drawn to marine and aquatic life who want to study ocean and freshwater ecosystems firsthand.", field="Aquatic Biology"),
    _p("ucsb-zoology-bs", _LS, "Bachelor of Science in Zoology", "bachelors", "Department of Ecology, Evolution, and Marine Biology", "26.07",
       "The study of animal biology — form, function, behavior, and evolution — from invertebrates to vertebrates, with field and laboratory work.",
       "Students fascinated by animals and their biology, behavior, and evolution.", field="Zoology"),
    _p("ucsb-eemb-phd", _LS, "Doctor of Philosophy in Ecology, Evolution, and Marine Biology", "phd", "Department of Ecology, Evolution, and Marine Biology", "26.13",
       "A funded doctorate in ecology, evolution, and marine biology, tied to the Marine Science Institute and coastal reserves, with global-change and marine-ecology strengths.",
       "Aspiring ecologists and marine biologists seeking a funded doctorate with strong field and marine research.", field="Ecology, Evolution, and Marine Biology"),
    _p("ucsb-marine-science-ms", _LS, "Master of Science in Marine Science", "masters", "Interdepartmental Graduate Program in Marine Science", "26.13",
       "An interdisciplinary graduate program in marine science spanning biology, chemistry, geology, and physics of the ocean, based at the Marine Science Institute.",
       "Graduates seeking interdisciplinary ocean-science training across biological, chemical, geological, and physical oceanography.", field="Marine Science"),
    _p("ucsb-marine-science-phd", _LS, "Doctor of Philosophy in Marine Science", "phd", "Interdepartmental Graduate Program in Marine Science", "26.13",
       "A funded interdisciplinary doctorate in ocean science, integrating biological, chemical, geological, and physical oceanography at the Marine Science Institute.",
       "Aspiring ocean scientists seeking a funded interdisciplinary doctorate in marine science.", field="Marine Science"),
    _p("ucsb-environmental-studies-ba", _LS, "Bachelor of Arts in Environmental Studies", "bachelors", "Environmental Studies Program", "03.01",
       "An interdisciplinary major combining natural science, social science, and policy to understand and address environmental problems, in a pioneering program.",
       "Students who want to work on environmental problems across science, policy, and society.", field="Environmental Studies"),
    _p("ucsb-dynamical-neuroscience-phd", _LS, "Doctor of Philosophy in Dynamical Neuroscience", "phd", "Interdepartmental Graduate Program in Dynamical Neuroscience", "26.15",
       "An interdisciplinary funded doctorate applying quantitative and computational methods to neuroscience, bridging brain sciences, physics, and engineering.",
       "Aspiring computational neuroscientists seeking a quantitative, interdisciplinary doctorate.", field="Dynamical Neuroscience"),
    _p("ucsb-quantitative-biosciences-phd", _LS, "Doctor of Philosophy in Quantitative Biosciences", "phd", "Interdisciplinary Program in Quantitative Biosciences", "26.12",
       "An interdisciplinary funded doctorate integrating biology with mathematics, physics, and computation to study living systems quantitatively.",
       "Aspiring quantitative biologists who want to study living systems with mathematical and computational tools.", field="Quantitative Biosciences"),

    # ══════════ Robert Mehrabian College of Engineering ══════════
    _p("ucsb-computer-science-bs", _ENGR, "Bachelor of Science in Computer Science", "bachelors", "Department of Computer Science", "11.07",
       "The theory and practice of computing — algorithms, systems, software, and machine learning — in a nationally ranked department with strong research ties.",
       "Students who want a rigorous computer-science degree with strong systems, graphics, and machine-learning research and top salary outcomes.", field="Computer Science"),
    _p("ucsb-computer-engineering-bs", _ENGR, "Bachelor of Science in Computer Engineering", "bachelors", "Department of Electrical and Computer Engineering", "14.09",
       "The design of computing hardware and systems at the boundary of electrical engineering and computer science — digital design, architecture, and embedded systems.",
       "Students who want to build computing systems from circuits to software at the hardware-software boundary.", field="Computer Engineering"),
    _p("ucsb-electrical-engineering-bs", _ENGR, "Bachelor of Science in Electrical Engineering", "bachelors", "Department of Electrical and Computer Engineering", "14.10",
       "The study of electronics, signals, communications, photonics, and control, in a department with a Nobel legacy in semiconductor heterostructures.",
       "Students drawn to electronics, communications, photonics, and control who want a research-active electrical-engineering program.", field="Electrical Engineering"),
    _p("ucsb-mechanical-engineering-bs", _ENGR, "Bachelor of Science in Mechanical Engineering", "bachelors", "Department of Mechanical Engineering", "14.19",
       "The design and analysis of mechanical and thermal systems — mechanics, dynamics, thermodynamics, and controls — with strong ties to materials and robotics.",
       "Students who want to design machines and systems, from mechanics and dynamics to energy and robotics.", field="Mechanical Engineering"),
    _p("ucsb-chemical-engineering-bs", _ENGR, "Bachelor of Science in Chemical Engineering", "bachelors", "Department of Chemical Engineering", "14.07",
       "The application of chemistry, physics, and mathematics to the design of processes that transform materials and energy, with strengths in biomolecular and materials engineering.",
       "Students who want to engineer processes and materials at the intersection of chemistry, biology, and physics.", field="Chemical Engineering"),
    _p("ucsb-artificial-intelligence-bs", _ENGR, "Bachelor of Science in Artificial Intelligence", "bachelors", "Department of Computer Science", "11.01",
       "A degree focused on the foundations and applications of artificial intelligence — machine learning, reasoning, perception, and the responsible use of AI.",
       "Students who want to specialize in artificial intelligence and machine learning from a computing foundation.", field="Artificial Intelligence"),
    _p("ucsb-computer-science-ms", _ENGR, "Master of Science in Computer Science", "masters", "Department of Computer Science", "11.07",
       "Advanced computer-science coursework and research — systems, security, graphics, databases, and machine learning — earned toward industry or the doctorate.",
       "Graduates deepening computer-science expertise for advanced industry roles or doctoral study.", field="Computer Science"),
    _p("ucsb-computer-science-phd", _ENGR, "Doctor of Philosophy in Computer Science", "phd", "Department of Computer Science", "11.07",
       "A funded doctorate with strengths in systems, security, computer graphics, databases, and machine learning, in a nationally ranked department.",
       "Aspiring computer scientists seeking a funded research doctorate in systems, security, graphics, or machine learning.", field="Computer Science"),
    _p("ucsb-electrical-computer-engineering-ms", _ENGR, "Master of Science in Electrical and Computer Engineering", "masters", "Department of Electrical and Computer Engineering", "14.10",
       "Advanced study in electronics, communications, photonics, signal processing, and computer engineering, earned toward industry or the doctorate.",
       "Graduates deepening electrical- and computer-engineering expertise for advanced industry roles or doctoral study.", field="Electrical and Computer Engineering"),
    _p("ucsb-electrical-computer-engineering-phd", _ENGR, "Doctor of Philosophy in Electrical and Computer Engineering", "phd", "Department of Electrical and Computer Engineering", "14.10",
       "A funded doctorate in electrical and computer engineering, with world-leading photonics and semiconductor research and a Nobel heterostructure legacy.",
       "Aspiring electrical and computer engineers seeking a top research doctorate, especially in photonics and semiconductors.", field="Electrical and Computer Engineering"),
    _p("ucsb-mechanical-engineering-ms", _ENGR, "Master of Science in Mechanical Engineering", "masters", "Department of Mechanical Engineering", "14.19",
       "Advanced study in solid mechanics, dynamics and control, thermal sciences, and robotics, earned toward industry or the doctorate.",
       "Graduates deepening mechanical-engineering expertise for advanced industry roles or doctoral study.", field="Mechanical Engineering"),
    _p("ucsb-mechanical-engineering-phd", _ENGR, "Doctor of Philosophy in Mechanical Engineering", "phd", "Department of Mechanical Engineering", "14.19",
       "A funded doctorate spanning solid mechanics, dynamics and control, fluids and thermal sciences, and robotics, with strong materials ties.",
       "Aspiring mechanical engineers seeking a funded research doctorate with strengths in controls, robotics, and materials.", field="Mechanical Engineering"),
    _p("ucsb-chemical-engineering-phd", _ENGR, "Doctor of Philosophy in Chemical Engineering", "phd", "Department of Chemical Engineering", "14.07",
       "A funded doctorate with recognized strengths in biomolecular engineering, soft materials, and complex fluids, tied to UCSB's materials and nanoscience institutes.",
       "Aspiring chemical engineers seeking a top research doctorate in biomolecular engineering and soft materials.", field="Chemical Engineering"),
    _p("ucsb-bioengineering-phd", _ENGR, "Doctor of Philosophy in Bioengineering", "phd", "Department of Bioengineering", "14.05",
       "A funded interdisciplinary doctorate applying engineering to biology and medicine — biomolecular, cellular, and systems bioengineering — across engineering and the life sciences.",
       "Aspiring bioengineers seeking an interdisciplinary doctorate at the interface of engineering, biology, and medicine.", field="Bioengineering"),
    _p("ucsb-materials-ms", _ENGR, "Master of Science in Materials", "masters", "Materials Department", "40.10",
       "Advanced study of the structure, properties, and processing of materials — electronic, structural, and soft materials — in a nationally top-ranked department.",
       "Graduates deepening materials expertise for advanced industry roles or doctoral study.", field="Materials"),
    _p("ucsb-materials-phd", _ENGR, "Doctor of Philosophy in Materials", "phd", "Materials Department", "40.10",
       "A #3-nationally-ranked, funded doctorate on the structure, properties, and processing of materials, anchored by an NSF Materials Research Laboratory and a blue-LED Nobel legacy.",
       "Aspiring materials scientists and engineers seeking a top-3 research doctorate spanning electronic, structural, and soft materials.", field="Materials"),
    _p("ucsb-media-arts-technology-ms", _ENGR, "Master of Science in Media Arts and Technology", "masters", "Media Arts and Technology Program", "09.07",
       "An interdisciplinary graduate program fusing media art, music, engineering, and computing — home to the immersive AlloSphere instrument.",
       "Graduates working at the intersection of art, music, and technology, from interactive media to computer music.", field="Media Arts and Technology"),
    _p("ucsb-media-arts-technology-phd", _ENGR, "Doctor of Philosophy in Media Arts and Technology", "phd", "Media Arts and Technology Program", "09.07",
       "A funded interdisciplinary doctorate integrating media art, music, engineering, and computing, with research in immersive media, sonification, and interactive systems.",
       "Aspiring researchers at the art-and-technology frontier seeking an interdisciplinary media-arts doctorate.", field="Media Arts and Technology"),
    _p("ucsb-technology-management-mtm", _ENGR, "Master of Technology Management", "masters", "Technology Management Program", "52.13",
       "A professional degree pairing engineering and science backgrounds with management, entrepreneurship, and product leadership, based in UCSB's Technology Management Program.",
       "Engineers and scientists who want management, entrepreneurship, and product-leadership skills to move into technology leadership.", field="Technology Management"),
    _p("ucsb-technology-management-phd", _ENGR, "Doctor of Philosophy in Technology Management", "phd", "Technology Management Program", "52.13",
       "A funded doctorate researching the management of technology and innovation — entrepreneurship, strategy, and the commercialization of science and engineering.",
       "Aspiring scholars of technology management and innovation seeking a research doctorate.", field="Technology Management"),

    # ══════════ College of Creative Studies ══════════
    _p("ucsb-ccs-computing-bs", _CCS, "Bachelor of Science in Computing (College of Creative Studies)", "bachelors", "College of Creative Studies", "11.01",
       "A small, research-intensive computing major in the College of Creative Studies, where students pursue advanced, self-directed computer-science work from early on.",
       "Highly self-directed students who want to dive into advanced computing research and projects from their first year.", field="Computing"),
    _p("ucsb-ccs-marine-science-bs", _CCS, "Bachelor of Science in Marine Science (College of Creative Studies)", "bachelors", "College of Creative Studies", "26.13",
       "An intensive, research-based marine-science major in the College of Creative Studies, immersing students in original ocean research alongside UCSB's marine scientists.",
       "Students passionate about the ocean who want to do original marine research early in a small, mentored college.", field="Marine Science"),
    _p("ucsb-ccs-writing-literature-ba", _CCS, "Bachelor of Arts in Writing and Literature (College of Creative Studies)", "bachelors", "College of Creative Studies", "23.13",
       "A creative-writing-centered major in the College of Creative Studies, where students build a serious body of original work across genres with close faculty mentorship.",
       "Serious young writers who want to focus on producing original creative work in a small, workshop-driven college.", field="Writing and Literature"),
    _p("ucsb-ccs-music-composition-bm", _CCS, "Bachelor of Music in Music Composition (College of Creative Studies)", "bachelors", "College of Creative Studies", "50.09",
       "A composition-focused degree in the College of Creative Studies, where student composers produce and hear original works in a mentored, creation-first environment.",
       "Emerging composers who want to write, produce, and hear original music from their first year.", field="Music Composition"),

    # ══════════ Bren School of Environmental Science and Management ══════════
    _p("ucsb-environmental-science-management-mesm", _BREN, "Master of Environmental Science and Management", "masters", "Bren School of Environmental Science and Management", "03.01",
       "A leading two-year professional master's pairing rigorous environmental science with economics, policy, and management, built around a year-long interdisciplinary group project for a real client.",
       "Aspiring environmental professionals who want to combine science with policy and management and solve real problems for clients.", field="Environmental Science and Management", months=24),
    _p("ucsb-environmental-data-science-meds", _BREN, "Master of Environmental Data Science", "masters", "Bren School of Environmental Science and Management", "30.70",
       "An intensive one-year professional master's in environmental data science, training students in programming, statistics, and machine learning applied to environmental problems.",
       "Environmental scientists and analysts who want strong data-science skills — coding, statistics, and machine learning — for environmental work.", field="Environmental Data Science", months=12),
    _p("ucsb-environmental-science-management-phd", _BREN, "Doctor of Philosophy in Environmental Science and Management", "phd", "Bren School of Environmental Science and Management", "03.01",
       "A funded doctorate advancing interdisciplinary research on environmental problems across natural science, economics, and policy at a top environmental school.",
       "Aspiring environmental researchers who want an interdisciplinary doctorate spanning science, economics, and policy.", field="Environmental Science and Management"),

    # ══════════ Gevirtz Graduate School of Education ══════════
    _p("ucsb-education-ma", _GGSE, "Master of Arts in Education", "masters", "Department of Education", "13.01",
       "Advanced study of learning, teaching, and educational research earned toward the doctorate or professional practice, in a graduate-only school of education.",
       "Educators and future researchers deepening their study of learning, teaching, and education policy.", field="Education"),
    _p("ucsb-education-phd", _GGSE, "Doctor of Philosophy in Education", "phd", "Department of Education", "13.01",
       "A funded doctorate preparing education researchers and scholars across learning, teaching, policy, and educational equity.",
       "Aspiring education researchers and scholars seeking a funded doctorate across learning, policy, and equity.", field="Education"),
    _p("ucsb-teacher-education-med", _GGSE, "Master of Education (Teacher Education Program)", "masters", "Teacher Education Program", "13.12",
       "A professional program combining a California teaching credential with a master's degree, preparing teachers through coursework and supervised classroom placements.",
       "Aspiring K–12 teachers who want a California credential paired with a master's degree.", field="Teacher Education", months=12),
    _p("ucsb-counseling-clinical-school-psychology-phd", _GGSE, "Doctor of Philosophy in Counseling, Clinical, and School Psychology", "phd", "Department of Counseling, Clinical, and School Psychology", "42.28",
       "A funded doctorate in a nationally regarded department training researchers and practitioners in counseling, clinical, and school psychology.",
       "Aspiring psychologists seeking a research-and-practice doctorate in counseling, clinical, or school psychology.", field="Counseling, Clinical, and School Psychology"),
    _p("ucsb-school-psychology-med", _GGSE, "Master of Education in School Psychology", "masters", "Department of Counseling, Clinical, and School Psychology", "42.28",
       "A professional program preparing school-psychology practitioners to support student learning, behavior, and mental health in K–12 settings.",
       "Future school psychologists who want professional training to support students' learning and well-being.", field="School Psychology"),
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# ── Build-time self-checks (fail the build on any structural defect) ────────
_dupe_slugs = [s for s in PROGRAM_SLUGS if PROGRAM_SLUGS.count(s) > 1]
if _dupe_slugs:
    raise ValueError(f"UCSB catalog has duplicate slugs: {sorted(set(_dupe_slugs))[:8]}")
_name_key = [(p["program_name"], p["degree_type"]) for p in PROGRAMS]
_dupe_names = [k for k in _name_key if _name_key.count(k) > 1]
if _dupe_names:
    raise ValueError(f"UCSB catalog has duplicate (program_name, degree_type): {sorted(set(_dupe_names))[:8]}")
_cip_missing = [p["slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    raise ValueError(f"UCSB catalog missing cip_code on {len(_cip_missing)} rows: {_cip_missing[:8]}")
_who_missing = [p["slug"] for p in PROGRAMS if not p.get("who")]
if _who_missing:
    raise ValueError(f"UCSB catalog missing who_its_for on {len(_who_missing)} rows: {_who_missing[:8]}")
_no_dept = [p["slug"] for p in PROGRAMS if not p.get("department")]
if _no_dept:
    raise ValueError(f"UCSB catalog missing department on {len(_no_dept)} rows: {_no_dept[:8]}")
_bad_school = [p["slug"] for p in PROGRAMS if p["school"] not in {s["name"] for s in SCHOOLS}]
if _bad_school:
    raise ValueError(f"UCSB catalog references unknown school on: {_bad_school[:8]}")


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich UC Santa Barbara to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when the institution is absent — safe on fresh/CI databases.
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
    # Lead media_gallery with the verified hero campus photo; keep prior entries behind it.
    # (The explore-card image_url + hero derive from school_outcomes.campus_photos[0], set above.)
    hero = _CAMPUS_PHOTOS[0]["url"]
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
        p.tuition = _resolve_tuition(spec)
        p.cost_data = _cost_data(spec)
        p.application_requirements = _requirements_for(spec)
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if fos is not None:
            salary, cip = fos
            p.outcomes_data = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "conditions": "College Scorecard Field of Study median earnings one year after completion (UNITID 110705).",
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?110705",
            }
        else:
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        p.outcomes_data["_standard"] = _program_standard(spec)
        p.cip_code = spec["cip"]
        p.who_its_for = spec["who"]
        p.tracks = spec.get("tracks")
        p.class_profile = None
        p.faculty_contacts = None
        p.external_reviews = _REVIEWS_BY_SLUG.get(spec["slug"])
        if spec["degree_type"] == "bachelors":
            p.application_deadline = date(2026, 11, 30)
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
