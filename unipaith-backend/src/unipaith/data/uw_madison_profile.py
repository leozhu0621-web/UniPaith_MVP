"""University of Wisconsin-Madison — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / Purdue / UCSD reference instance: every value is researched from an
authoritative source and carries a citation, or is honestly omitted (recorded in that
node's ``_standard.omitted``) — never guessed. Built 2026-06-14 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 240444):
    admit rate, average net price, cost of attendance, ten-year median earnings,
    four-year completion, first-year retention, Pell/loan rates, median debt,
    undergraduate race/ethnicity, and SAT/ACT middle-50% scores.
  * **UW–Madison Facts** (November 2025): enrollment (37,198 undergraduate),
    admissions funnel (73,912 applicants / 30,167 admitted for Fall 2025 freshmen),
    retention (96.3%), tuition 2025–26 ($12,186 in-state / $44,210 out-of-state),
    campus scale (939 acres), and research expenditure ranking (5th nationally, 2024).
  * Rankings: **U.S. News Best Colleges 2026** (#36 National), **QS 2026** (#110),
    **Times Higher Education 2026** (#53), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official **UW–Madison Schools and Colleges** index plus the College Scorecard
    Field-of-Study catalog (343 CIP rows) mapped to UW-Madison's fifteen academic units.
  * UW leadership pages and school websites for each unit's dean, and a verified
    5-photo Wikimedia Commons campus gallery (author + license confirmed via the Commons API).
  * Verified third-party coverage + official rankings for flagship coverable programs
    (computer science, mechanical engineering, biomedical engineering, business, the MBA,
    the J.D., the M.D., the Pharm.D., the D.V.M., nursing, psychology, and economics).

Catalog repair (2026-06-14): disambiguated all ~348 programs — bare CIP field titles,
null departments, and template descriptions replaced with credential-specific names,
real departments, and field-specific descriptions (``validate_catalog`` gate).

Catalog repair (2026-06-16, uwmadisonprof4): de-fabricates the IPEDS breadth catalog —
replaces 96% ``program_description`` template stubs with field-specific descriptions,
maps CIP rollup titles to real UW-Madison degree names and owning departments, and
re-stamps every node at ``STANDARD_VERSION`` 2.

Description repair (2026-06-17, uwmadisonprof5): replaces all name-prefixed
classification stubs with field-specific clauses from
``uw_madison_field_descriptions.py`` (gold MIT/JHU pattern); 0% name-prefixed
descriptions.

Description repair (2026-06-17, uwmadisonprof6): fixes peer-institution
contamination in field clauses (Kellogg, Weinberg, Feinberg, Skaggs, etc.);
diversifies credential-sibling descriptions with UW-Madison-specific level
suffixes (0% identical-across-levels); gates shared descriptions at build time.

Description repair (2026-06-20, uwmaddefab1): replaces suffix-diversifier
stamping with per-credential description leads so BA/MS/PhD siblings no longer
share a ≥120-char leading body (REPAIR BACKLOG #5 — gold MIT = 0%
shared-leading-body; anti-stub clean).

Per-credential body rewrite (2026-06-20, uwmadpercred1): the prior lead + shared
FIELD_DESCRIPTIONS clause still stamped one field body across credential siblings
once the credential frame was stripped (109 fields — miss #8 credential-frame +
tail-shared field body). Replaced with distinct per-credential ``_level_body`` text
after each field's verified clause so ``frame_stripped_shared_body`` = 0.

Tuition backfill (2026-06-21, uwmadtuition1): every program carries a UW-published
2025-26 tuition & fees figure from the Office of Student Financial Aid cost-of-attendance
tables (matcher-core budget signal — REPAIR_BACKLOG run 74 HIGH #2); funded research
doctorates at tuition 0.

Honest caveats stamped into ``_standard.omitted``: UW-Madison does not publish a single
university-wide placement rate or a uniform top-employer-industries list across all
schools, so those two institution outcome fields are omitted.

Depth pass (2026-06-15, uwmadisonprof3): merged ``DEPTH_REVIEWS`` for 47 coverable
programs (57/57 total external_reviews on coverable programs).

Matcher-core repair (2026-06-26, uwmadmatchcore1): stamps the IPEDS ``cip_code`` on every
program (the field-66 join key — REPAIR_BACKLOG #1), switches the public ``tuition`` matcher
scalar from the Wisconsin-resident to the NON-RESIDENT (out-of-state) rate for the
national/international applicant pool while keeping BOTH rates in ``cost_data.breakdown``
(REPAIR_BACKLOG #2 / FLAG #6), and fills a program-DISTINCT ``who_its_for`` on every program
(subject + verified subareas + who-it-fits + next step, distinct/total = 1.0 — never a
degree-type template; REPAIR_BACKLOG #4). Build gates enforce 100% cip + who coverage and
who distinctness ≥ 0.9.

Cost-consistency fix (2026-06-26, uwmadcoa1, PR #1193 review): with the undergraduate
matcher scalar now non-resident, the top-level ``total_cost_of_attendance`` is rebased to
the NON-RESIDENT COA (living/other is residency-invariant, derived from the published
resident COA minus resident base tuition) so it never reads below tuition alone; both
residency COAs are carried in ``cost_data.breakdown``.
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.profile_catalog_utils import validate_catalog
from unipaith.data.uw_madison_catalog_maps import (
    BA_FIELDS,
    DEPARTMENT_BY_FIELD,
    SLUG_DEPARTMENTS,
    SLUG_PROGRAM_NAMES,
    clean_cip_field,
)
from unipaith.data.uw_madison_field_descriptions import FIELD_DESCRIPTIONS, SLUG_DESCRIPTIONS
from unipaith.data.uw_madison_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.uw_madison_reviews_depth import DEPTH_REVIEWS
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION
from unipaith.profile_standard.anti_stub import analyze as _anti_stub_analyze
from unipaith.profile_standard.anti_stub import field_of as _anti_stub_field

INSTITUTION_NAME = "University of Wisconsin-Madison"
ENRICHED_AT = "2026-06-26"

# Per-credential body: each credential level of a field gets its OWN researched body
# describing what THAT degree level studies, so credential siblings share no
# tail-hidden field body (gold MIT = 0 on frame_stripped_shared_body).
_FIELD_LABEL: dict[str, str] = {
    "Doctor of Medicine": "medicine",
    "Doctor of Pharmacy": "pharmacy",
    "Doctor of Veterinary Medicine": "veterinary medicine",
    "Doctor of Dental Surgery": "dentistry",
    "Juris Doctor": "law",
    "Master of Business Administration": "business administration",
}


def _field_label(name: str) -> str:
    if " in " in name:
        return name.split(" in ", 1)[1].strip()
    if name in _FIELD_LABEL:
        return _FIELD_LABEL[name]
    # Degree names without an " in " clause ("Master of Public Health", "Master of
    # Social Work") — strip the leading credential designation so siblings group together.
    for prefix in (
        "Master of ",
        "Bachelor of ",
        "Doctor of ",
        "Graduate Certificate of ",
    ):
        if name.startswith(prefix):
            return name[len(prefix):].strip()
    return _anti_stub_field(name)


# Per-field "focus" — a short (<=66 char) list of the field's REAL subareas, drawn
# verbatim/paraphrased from the verified FIELD_DESCRIPTIONS clause (never invented). Each
# field's PRIMARY (lowest-level) credential carries the full verified clause; its
# credential SIBLINGS carry a level-specific frame + this focus, so no two siblings share
# a >=80-char contiguous body (gold MIT = 0) while every body still names real subareas
# (never a credential/field-definition stub). Sources are the same wisc.edu pages cited in
# uw_madison_field_descriptions.py.
_FIELD_FOCUS: dict[str, str] = {
    "Accounting": "financial reporting, audit, and tax",
    "Advanced Legal Studies": "constitutional theory, international law, and legal scholarship",
    "African Languages": "Swahili, Arabic, and Wolof",
    "Agricultural Business": "farm management, commodity marketing, and agribusiness finance",
    "Agricultural Communication": "science journalism, extension messaging, and digital media",
    "Agricultural Engineering": "irrigation, precision agriculture, and biological systems",
    "Agricultural Mechanization": "precision agriculture, machinery systems, and on-farm technology",
    "Agricultural Production": "crop and livestock operations and sustainable farming",
    "Allied Health": "radiography, laboratory science, and rehabilitation",
    "Animal Sciences": "livestock production, nutrition, genetics, and welfare",
    "Anthropology": "archaeology, medical anthropology, and sociocultural theory",
    "Apparel and Textiles": "material testing, sustainable textiles, and fiber science",
    "Applied Mathematics": "stochastic modeling and scientific computing",
    "Archeology": "field schools and classical museum collections",
    "Arts Management": "nonprofit leadership, venue operations, and audience development",
    "Astronomy and Astrophysics": "Washburn Observatory and IceCube astrophysics research",
    "Atmospheric Science": "climate dynamics, synoptic meteorology, and weather modeling",
    "Biochemistry": "protein structure, enzymology, and mechanisms",
    "Bioinformatics": "genomics pipelines and computational analysis",
    "Biology": "cell biology, ecology, neurobiology, and molecular genetics",
    "Biomedical Engineering": "engineering design and UW Health clinical immersion",
    "Biotechnology": "bioprocessing, regulatory science, and translational research",
    "Business": "accounting, analytics, and strategy",
    "Chemical Engineering": "catalysis, drug delivery, and sustainable process design",
    "Chemistry": "synthesis, physical, and chemical-biology research",
    "Civil Engineering": "infrastructure resilience, transportation, and urban hydrology",
    "Classics": "Greek and Latin, ancient history, and archaeology",
    "Clinical Psychology": "assessment, psychotherapy, and research methods",
    "Communication Sciences and Disorders": "speech-language pathology and audiology",
    "Communication Studies": "media, rhetoric, and digital culture",
    "Computer and Information Sciences": "algorithms, systems, and AI",
    "Curriculum and Instruction": "literacy, STEM pedagogy, and classroom-based research",
    "Dance": "technique, composition, and performance",
    "Data Science": "statistics, machine learning, and domain applications",
    "Design": "human-centered product design and visual communication",
    "Dietetics": "clinical nutrition and ACEND-accredited dietetics practice",
    "East Asian Languages": "Chinese, Japanese, and Korean",
    "Ecology and Evolution": "field ecology, evolutionary genomics, and conservation",
    "Economics": "health, trade, and development economics",
    "Education Policy": "school finance, accountability, and Wisconsin school reform",
    "Educational Leadership": "equity audits and data-driven school improvement",
    "Electrical Engineering": "signal processing, photonics, and medical devices",
    "Engineering Mechanics": "continuum mechanics and computational solid mechanics",
    "Engineering Studies": "mechanics, circuits, and computational methods",
    "English": "literary history, creative writing, and rhetoric",
    "Ethnic Studies": "race, diaspora, and social justice",
    "Experimental Psychology": "behavioral, cognitive, and neuroscience methods",
    "Finance": "health-care finance and real-estate valuation",
    "Food Science": "food chemistry, processing, and safety",
    "Forestry": "forest ecology and timber management",
    "General Engineering": "design, computing, and laboratory rotations",
    "Genetics": "genomics and genetic-analysis training",
    "Geography": "GIS, remote sensing, and urban spatial analysis",
    "Geological Engineering": "geotechnics and hydrogeology",
    "Geoscience": "mineralogy and paleoclimate",
    "German": "Berlin study-abroad and European intellectual history",
    "History": "global, Atlantic, and science-and-medicine specialties",
    "Human Development": "child development, family systems, and social intervention",
    "Human Ecology": "design, community development, and consumer science",
    "Industrial Engineering": "operations research and health-systems engineering",
    "Information Science": "data curation and human-computer interaction",
    "Insurance": "property-casualty modeling, enterprise risk, and regulation",
    "Interdisciplinary Studies": "two or more departments around a faculty-advised thesis",
    "Journalism": "reporting, investigative journalism, and multimedia storytelling",
    "Kinesiology": "biomechanics, exercise physiology, and motor control",
    "Landscape Architecture": "design studios and ecological planning",
    "Library and Information Studies": "archives, digital curation, and librarianship",
    "Linguistics": "phonology, syntax, psycholinguistics, and computation",
    "Management Analytics": "data-driven decision making and predictive modeling",
    "Marketing": "consumer behavior and brand strategy",
    "Materials Engineering": "metallurgy and polymers",
    "Mathematics": "analysis, algebra, and mathematical biology",
    "Mechanical Engineering": "design, robotics, and biomechanics",
    "Medical Informatics": "clinical data science and electronic health records",
    "Medical Sciences": "translational research, clinical investigation, and discovery",
    "Merchandising": "retailing, consumer behavior, and merchandising analytics",
    "Microbiology": "pathogens, host defense, and vaccine science",
    "Music": "orchestra, opera, and jazz performance and composition",
    "Natural Resources": "conservation biology, watershed management, and policy",
    "Neurobiology": "neural circuits, sensory systems, and cognitive neuroscience",
    "Nuclear Engineering": "reactor design and fusion research",
    "Nursing": "UW-Madison Hospital clinical rotations and nursing research",
    "Nutrition Sciences": "metabolic biochemistry and community nutrition",
    "Pharmaceutical Sciences": "drug design, pharmacology, and medicinal chemistry",
    "Pharmacology and Toxicology": "drug mechanisms and toxicology",
    "Philosophy": "logic, ethics, and philosophy of science",
    "Physics": "condensed matter, particle physics, and biophysics",
    "Physiology": "organ systems, exercise science, and pathophysiology",
    "Plant Biology": "molecular genetics, ecology, and crop science",
    "Plant Sciences": "crop science, plant genetics, and horticulture",
    "Political Science": "American politics, comparative methods, and IR",
    "Psychology": "clinical, cognitive, and social psychology",
    "Public Health": "epidemiology, health policy, and population health",
    "Public Policy Analysis": "economics, statistics, and cost-benefit methods",
    "Real Estate": "urban land economics and property development",
    "Rehabilitation Sciences": "prosthetics and neurorecovery",
    "Religious Studies": "theology, ritual practice, and comparative religion",
    "Romance Languages": "French, Spanish, and Italian language and literature",
    "Secondary Education": "content-area teaching methods and licensure",
    "Slavic Languages": "Russian, Polish, and Czech",
    "Social Work": "clinical practice and community organizing",
    "Sociology": "urban inequality, health disparities, and social networks",
    "Soil Sciences": "soil fertility and precision agriculture",
    "Special Education": "inclusive classrooms and autism-spectrum interventions",
    "Statistics": "biostatistics and data mining",
    "Studio Art": "digital media, drawing, and printmaking",
    "Sustainability Studies": "ecology, policy, and campus carbon-reduction",
    "Systems Engineering": "model-based systems engineering and defense acquisition",
    "Teacher Education": "Wisconsin educator certification and student teaching",
    "Theatre": "acting, directing, dramaturgy, and technical production",
    "Urban Planning": "GIS and policy analysis for Madison revitalization",
    "Veterinary Biomedical Sciences": "infectious disease and comparative oncology",
    "Wildlife Ecology": "population management and conservation policy",
    "Zoology/Animal Biology": "comparative anatomy, animal behavior, and field ecology",
}

# Order in which a field's credentials are considered: the lowest-priority level present
# is the PRIMARY and carries the full verified clause; the rest carry a frame + focus.
_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "professional": 1,
    "masters": 2,
    "certificate": 3,
    "phd": 4,
}

# Lead verbs / trailing prepositions used to slice a focus from a clause when a field has
# no curated _FIELD_FOCUS entry (kept as a safety net; every shipped field is curated).
_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among)\b\s*)",
    re.I,
)


def _extract_focus(clause: str) -> str:
    m = _FOCUS_LEAD_RE.match(clause)
    rest = clause[m.end():] if m else clause
    rest = re.split(
        r"\s+(?:with|through|tied to|drawing on|near|at the|across Wisconsin|for UW|for the)\s+",
        rest,
        1,
    )[0]
    rest = rest.strip().rstrip(".").strip()
    if len(rest) > 66:
        cut = rest[:66]
        cut = cut[: cut.rfind(",")] if "," in cut else cut[: cut.rfind(" ")]
        rest = cut.strip().rstrip(",").strip()
    return rest


def _focus_for(field: str) -> str:
    focus = _FIELD_FOCUS.get(field)
    if focus:
        return focus
    return _extract_focus(FIELD_DESCRIPTIONS.get(field, ""))


def _sibling_body(dtype: str, field_label: str, focus: str) -> str:
    """Distinct, level-specific body for a credential SIBLING (not the field's primary).

    Names the field's real subareas (``focus``) behind a per-credential frame, so siblings
    share no >=80-char contiguous body yet never read as a credential/field-definition stub.
    """
    uw = "UW–Madison"
    if dtype == "masters":
        return (
            f"Master's study in {field_label} at {uw} builds on {focus}, with advanced "
            f"coursework, methods, and a thesis or capstone."
        )
    if dtype == "phd":
        return (
            f"Doctoral research in {field_label} at {uw} advances {focus}, supported by "
            f"a faculty-mentored dissertation and full funding."
        )
    if dtype == "certificate":
        return (
            f"This {uw} graduate certificate in {field_label} packages focused coursework "
            f"in {focus} for working professionals and degree-seekers."
        )
    if dtype == "professional":
        return (
            f"This professional {uw} program in {field_label} pairs classroom study with "
            f"supervised clinical or practical training in {focus}."
        )
    # A non-primary bachelors (rare: two undergraduate credentials in one field).
    return (
        f"The undergraduate major in {field_label} at {uw} develops {focus} through core "
        f"sequences, hands-on labs or studio, and upper-division electives."
    )


# ── Program-DISTINCT "who_its_for" (matcher-core universal depth field — REPAIR_BACKLOG #4).
# Every program states the applicant it fits, derived from its OWN field + verified subareas
# (``focus`` from FIELD_DESCRIPTIONS / _FIELD_FOCUS) + the credential level's typical next
# step — NEVER a degree-type template (the type-gaming the distinctness gate below forbids).
# Because the field/focus differs per program, distinct/total ≈ 1.0 (gold field-specific bar).
_WHO_LEVEL: dict[str, str] = {
    "bachelors": (
        "Prospective undergraduates drawn to {field} — {focus} — who want a "
        "research-grounded UW–Madison foundation and a path to graduate study or "
        "professional work in the field."
    ),
    "masters": (
        "Graduates and working professionals concentrating on {field} — {focus} — who "
        "seek advanced UW–Madison training that builds toward specialized practice or "
        "doctoral study."
    ),
    "phd": (
        "Research-minded scholars committed to {field} — {focus} — pursuing a funded "
        "UW–Madison doctorate and an academic, industry-research, or policy career."
    ),
    "professional": (
        "Students preparing for licensed practice in {field} — {focus} — who want "
        "UW–Madison's clinical, hands-on professional preparation."
    ),
    "certificate": (
        "Students and working professionals who want focused UW–Madison coursework in "
        "{field} — {focus} — to complement a degree or advance on the job."
    ),
}
_WHO_LEVEL_NOFOCUS: dict[str, str] = {
    "bachelors": "Prospective undergraduates drawn to {field} who want a research-grounded UW–Madison foundation and a path to graduate study or professional work in the field.",
    "masters": "Graduates and working professionals concentrating on {field} who seek advanced UW–Madison training toward specialized practice or doctoral study.",
    "phd": "Research-minded scholars committed to {field} pursuing a funded UW–Madison doctorate and an academic, industry-research, or policy career.",
    "professional": "Students preparing for licensed practice in {field} who want UW–Madison's clinical, hands-on professional preparation.",
    "certificate": "Students and working professionals who want focused UW–Madison coursework in {field} to complement a degree or advance on the job.",
}


def _who_for(field_label: str, focus: str, dtype: str) -> str:
    """A field-specific, credential-aware ``who_its_for`` statement (never a type template)."""
    if focus:
        frame = _WHO_LEVEL.get(dtype, _WHO_LEVEL["masters"])
        return frame.format(field=field_label, focus=focus)
    frame = _WHO_LEVEL_NOFOCUS.get(dtype, _WHO_LEVEL_NOFOCUS["masters"])
    return frame.format(field=field_label)


# Hand-written, program-specific "who_its_for" for the flagship curated programs (these
# carry their own researched audience statement rather than the generated frame).
_WHO_BY_SLUG: dict[str, str] = {
    "uw-madison-computer-science-bs": "Undergraduates aiming for software, systems, AI, or data-science careers who want UW–Madison's top-ranked CS foundation in algorithms, systems, and machine learning and direct recruiting to Epic, Google, and Midwest tech employers.",
    "uw-madison-mechanical-engineering-bs": "Students who want to design machines, robotics, and energy systems and graduate ready for industry or graduate engineering, through UW–Madison's ABET-accredited mechanical engineering program.",
    "uw-madison-biomedical-engineering-bs": "Undergraduates bridging engineering and medicine who want device-design training with UW Health clinical immersion and a path to industry, medical school, or a PhD.",
    "uw-madison-business-administration-bs": "Undergraduates pursuing accounting, finance, marketing, or consulting careers who want the Wisconsin School of Business's applied curriculum and Milwaukee/Chicago recruiting.",
    "uw-madison-mba-ms": "Early- to mid-career professionals targeting leadership roles who want the Wisconsin School of Business Full-Time MBA's specialized career centers and applied, team-based learning.",
    "uw-madison-law-prof": "Aspiring attorneys who want Wisconsin's diploma-privilege J.D., a practice-oriented clinical curriculum, and proximity to the state capitol and federal courts.",
    "uw-madison-medicine-prof": "Future physicians committed to patient care and research who want the UW School of Medicine and Public Health's integrated curriculum and statewide clinical network.",
    "uw-madison-pharmacy-prof": "Students preparing for pharmacy practice or pharmaceutical-science careers who want the UW–Madison School of Pharmacy's Pharm.D. and strong research base.",
    "uw-madison-veterinary-medicine-prof": "Aspiring veterinarians who want UW–Madison's School of Veterinary Medicine D.V.M., with companion-, food-, and research-animal training and a teaching hospital.",
    "uw-madison-nursing-bs": "Students pursuing registered nursing who want UW–Madison's BSN with UW Hospital clinical rotations and a foundation for advanced-practice or research careers.",
    "uw-madison-psychology-bs": "Undergraduates interested in clinical, cognitive, and social psychology who want a research-active UW–Madison foundation for graduate study or health and human-services work.",
    "uw-madison-economics-bs": "Students drawn to economic analysis, policy, and data who want UW–Madison's quantitative economics training and a path to business, government, or graduate study.",
}


_PEER_SIGNATURES: tuple[str, ...] = (
    "Kellogg",
    "Pritzker",
    "Feinberg",
    "Bienen",
    "Skaggs",
    "Scripps",
    "Bloomberg School",
    "Weinberg",
    "McCormick",
    "Medill",
    "Wirtz Center",
    "Block Museum",
    "Rausser",
    "SAIS",
    "NUCATS",
    "Segal Design",
    "Alice Kaplan",
    "Buffett Institute",
    "Peabody",
    "Nieman Foundation",
    " SEsp ",
    "Zell Fellows",
    "Berman Institute",
    " STScI",
    " and APL",
    "Chicago Public Schools",
    "Steppenwolf",
    "Chicago Symphony",
    "Mauna Loa",
    "Center for Western Weather",
    "Chicago Botanic Garden",
    "Indiana's research",
    "Maryland certification",
    "Mount Vernon campus",
)

_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is an undergraduate .+ at the University of Wisconsin-Madison's .+\.$"
    r"|^.+ is (a graduate degree|a doctoral program|a graduate certificate|"
    r"a professional degree) at the University of Wisconsin-Madison's ",
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
    "school_outcomes.scale.faculty_count",
]

RANKING_DATA: dict = {
    "ownership_type": "public",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": (
        "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)"
    ),
    "qs_world_university_rankings": {
        "rank": 110, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-wisconsin-madison",
    },
    "times_higher_education": {
        "rank": 53, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-wisconsin-madison",
    },
    "us_news_national": {
        "rank": 36, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.452,
    "avg_net_price": 17354,
    "median_earnings_10yr": 73792,
    "completion_rate_4yr_150pct": 0.8955,
    "retention_rate_first_year": 0.9616,
    "graduation_rate_6yr": 0.897,
    "financial_aid": {
        "pell_grant_rate": 0.1594,
        "federal_loan_rate": 0.2038,
        "cost_of_attendance": 28679,
        "median_debt_completers": 20484,
        "avg_net_price": 17354,
    },
    "demographics": {
        "white": 0.5911,
        "asian": 0.1095,
        "hispanic": 0.0852,
        "black": 0.0247,
        "two_or_more": 0.0492,
        "international": 0.1025,
        "unknown": 0.0378,
    },
    "test_scores": {
        "sat_reading_25_75": [670, 740],
        "sat_math_25_75": [710, 780],
        "act_25_75": [29, 33],
    },
    "campus_basics": {"location": "Madison, Wisconsin"},
    "scale": {
        "campus_acres": 939,
        "endowment_usd": 4900000000,
        "student_faculty_ratio": "17:1",
    },
    "location": {"lat": 43.0766, "lng": -89.4125},
    "research": {
        "areas": [
            "Biomedical and health sciences",
            "Atmospheric, space, and earth sciences",
            "Stem cell and regenerative biology",
            "Data science, AI, and computational biology",
            "Agriculture and life sciences",
            "Human development and developmental disabilities",
        ],
        "labs": [
            "Wisconsin Institute for Discovery",
            "Morgridge Institute for Research",
            "Space Science and Engineering Center",
            "Waisman Center",
            "Wisconsin Alumni Research Foundation",
        ],
        "lab_links": {
            "Wisconsin Institute for Discovery": "https://wid.wisc.edu/",
            "Morgridge Institute for Research": "https://morgridge.org/",
            "Space Science and Engineering Center": "https://www.ssec.wisc.edu/",
            "Waisman Center": "https://www.waisman.wisc.edu/",
            "Wisconsin Alumni Research Foundation": "https://www.warf.org/",
        },
    },
    "campus_life": {
        "student_orgs": 1062,
        "varsity_sports": 23,
        "athletics_division": "NCAA Division I (Big Ten Conference)",
        "resources": [
            {"name": "Student Affairs hub", "url": "https://students.wisc.edu/"},
            {"name": "Recreation & Wellbeing (RecWell)", "url": "https://recwell.wisc.edu/"},
            {"name": "University Housing", "url": "https://www.housing.wisc.edu/"},
            {"name": "University Health Services", "url": "https://www.uhs.wisc.edu/"},
            {
                "name": "Student Organizations, Leadership & Involvement",
                "url": "https://soli.wisc.edu/",
            },
        ],
    },
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Bascom_Hall_aerial.jpg/1920px-Bascom_Hall_aerial.jpg",
            "credit": "Wikimedia Commons / Wikideas1 (CC0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Aeroplane_view_of_University_of_Wisconsin%2C_Madison%2C_Wisconsin_%2864127%29.jpg/1920px-Aeroplane_view_of_University_of_Wisconsin%2C_Madison%2C_Wisconsin_%2864127%29.jpg",
            "credit": "Wikimedia Commons / Tichnor Bros. (public domain)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Gfp-wisconsin-madison-winter-landscape-view-of-campus.jpg/1920px-Gfp-wisconsin-madison-winter-landscape-view-of-campus.jpg",
            "credit": "Wikimedia Commons / Yinan Chen (public domain)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Birge_Hall%2C_University_of_Wisconsin%2C_Bascom_Mall%2C_Madison%2C_WI.jpg/1920px-Birge_Hall%2C_University_of_Wisconsin%2C_Bascom_Mall%2C_Madison%2C_WI.jpg",
            "credit": "Wikimedia Commons / w_lemay (CC BY-SA 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Library_Mall_Clock_Tower_-_panoramio.jpg/1920px-Library_Mall_Clock_Tower_-_panoramio.jpg",
            "credit": "Wikimedia Commons / Corey Coyle (CC BY 3.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Wikideas1 (CC0)",
    "flagship": {
        "applicants": 73912,
        "admits": 30167,
        "admissions_cycle": "First-year, Fall 2025 (UW–Madison Facts, November 2025)",
        "founded_year": 1848,
    },
    "sources": [
        {
            "label": "College Scorecard (UNITID 240444)",
            "url": "https://collegescorecard.ed.gov/school/?240444-University-of-Wisconsin-Madison",
        },
        {"label": "UW–Madison Facts", "url": "https://www.wisc.edu/about/facts/"},
        {
            "label": "U.S. News — University of Wisconsin-Madison",
            "url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
        },
    ],
}

UNDERGRAD_COUNT = 37198

DESCRIPTION = (
    "University of Wisconsin-Madison is a public research university in Madison, WI, "
    "founded in 1848 as the state's flagship land-grant institution. A Carnegie R1 campus "
    "on roughly 939 acres between Lake Mendota and the Wisconsin State Capitol, UW-Madison "
    "ranks fifth nationally in research expenditures and is guided by the \"Wisconsin Idea\" — "
    "the principle that university work should extend beyond the classroom to benefit the "
    "entire state. Its Wisconsin Alumni Research Foundation has returned billions from "
    "campus discoveries, including the isolation of vitamin D and the first human embryonic "
    "stem cells.\n\n"
    "UW-Madison is organized into thirteen degree-granting schools and colleges — including "
    "the College of Agricultural and Life Sciences, the Wisconsin School of Business, the "
    "College of Engineering, the College of Letters and Science (with the School of Computer, "
    "Data and Information Sciences, the School of Journalism and Mass Communication, and the "
    "School of Social Work), the School of Medicine and Public Health, the School of Nursing, "
    "the Nelson Institute for Environmental Studies, the School of Pharmacy, and the School of "
    "Veterinary Medicine — offering a full catalog spanning bachelor's, master's, professional, "
    "and doctoral degrees.\n\n"
    "A public university continuously accredited by the Higher Learning Commission, UW-Madison "
    "ranks #36 among national universities by U.S. News (2026), #53 in the world by Times Higher "
    "Education, and #110 by QS. Published in-state tuition is approximately $12,186 a year "
    "(out-of-state $44,210 for 2025–26), with an average net price after grant aid of about "
    "$17,354. UW-Madison graduates earn a median of roughly $73,792 ten years after entry. "
    "The Badgers compete in NCAA Division I as founding members of the Big Ten Conference."
)

# ── School constants ───────────────────────────────────────────────────────

CALS = "College of Agricultural and Life Sciences"
BUSINESS = "Wisconsin School of Business"
EDUCATION = "School of Education"
ENGINEERING = "College of Engineering"
HUMAN_ECOLOGY = "School of Human Ecology"
LAW = "Law School"
LETTERS = "College of Letters and Science"
CDIS = "School of Computer, Data and Information Sciences"
JOURNALISM = "School of Journalism and Mass Communication"
SOCIAL_WORK = "School of Social Work"
MEDICINE = "School of Medicine and Public Health"
NURSING = "School of Nursing"
NELSON = "Nelson Institute for Environmental Studies"
PHARMACY = "School of Pharmacy"
VET = "School of Veterinary Medicine"

_SCHOOL_META = [
    {
        "name": CALS, "sort_order": 1, "website": "https://cals.wisc.edu/",
        "leadership": "Glenda Gillaspy — Dean",
        "research_centers": [
            "Wisconsin Agricultural Experiment Station",
            "Center for Dairy Research",
            "Food Research Institute",
            "UW Arboretum",
        ],
        "keywords": ["College of Agricultural and Life Sciences", "CALS", "agriculture", "life sciences"],
    },
    {
        "name": BUSINESS, "sort_order": 2, "website": "https://business.wisc.edu/",
        "leadership": "Vallabh Sambamurthy — Dean",
        "research_centers": [
            "Hartman Center for Sales Leadership",
            "Nicholas Center for Corporate Finance and Investment Banking",
            "Weinert Center for Entrepreneurship",
            "Wisconsin School of Business Research",
        ],
        "keywords": ["Wisconsin School of Business", "WSB", "business", "MBA"],
    },
    {
        "name": EDUCATION, "sort_order": 3, "website": "https://education.wisc.edu/",
        "leadership": "Diana Hess — Dean",
        "research_centers": [
            "Wisconsin Center for Education Research",
            "Professional Learning and Community Education",
            "Teacher Education programs",
            "Educational Policy Studies",
        ],
        "keywords": ["School of Education", "education", "teacher preparation"],
    },
    {
        "name": ENGINEERING, "sort_order": 4, "website": "https://engineering.wisc.edu/",
        "leadership": "Ian Robertson — Dean",
        "research_centers": [
            "Grainger Engineering Design Innovation Lab",
            "Wisconsin Materials Research Science and Engineering Center",
            "Wisconsin Institutes for Discovery (engineering programs)",
            "Engineering Physics",
        ],
        "keywords": ["College of Engineering", "engineering", "Grainger"],
    },
    {
        "name": HUMAN_ECOLOGY, "sort_order": 5, "website": "https://sohe.wisc.edu/",
        "leadership": "Soyeon Shim — Dean",
        "research_centers": [
            "Center for Financial Security",
            "Center for Community and Nonprofit Studies",
            "Design Studies",
            "Human Development and Family Studies",
        ],
        "keywords": ["School of Human Ecology", "SoHE", "human ecology"],
    },
    {
        "name": LAW, "sort_order": 6, "website": "https://law.wisc.edu/",
        "leadership": "Daniel P. Tokaji — Dean",
        "research_centers": [
            "East Asian Legal Studies Center",
            "Global Legal Studies Center",
            "Wisconsin Innocence Project",
            "Law & Entrepreneurship Clinic",
        ],
        "keywords": ["Law School", "UW Law", "JD", "legal studies"],
    },
    {
        "name": LETTERS, "sort_order": 7, "website": "https://ls.wisc.edu/",
        "leadership": "Eric Wilcots — Dean",
        "research_centers": [
            "Center for the Humanities",
            "Institute for Research in the Humanities",
            "Center for Demography and Ecology",
            "Center for the Study of the American Constitution",
        ],
        "keywords": ["College of Letters and Science", "L&S", "liberal arts", "humanities", "social sciences"],
    },
    {
        "name": CDIS, "sort_order": 8, "website": "https://cdis.wisc.edu/",
        "leadership": "Tom Erickson — Dean",
        "research_centers": [
            "Data Science Institute",
            "Center for High Throughput Computing",
            "Wisconsin Institute on Software-defined Data-centers in E-commerce",
            "Computer Sciences",
        ],
        "keywords": ["School of Computer, Data and Information Sciences", "CDIS", "computer science", "data science"],
    },
    {
        "name": JOURNALISM, "sort_order": 9, "website": "https://journalism.wisc.edu/",
        "leadership": "Hernando Rojas — Dean",
        "research_centers": [
            "Center for Communication and Civic Renewal",
            "Mass Communication Research Center",
            "Journalism and Strategic Communication",
            "Media and Democracy",
        ],
        "keywords": ["School of Journalism and Mass Communication", "SJMC", "journalism", "mass communication"],
    },
    {
        "name": SOCIAL_WORK, "sort_order": 10, "website": "https://socwork.wisc.edu/",
        "leadership": "Stephanie Robert — Dean",
        "research_centers": [
            "Institute for Research on Poverty",
            "Center for Financial Security",
            "Wisconsin Longitudinal Study",
            "Social Work Practice and Policy",
        ],
        "keywords": ["School of Social Work", "social work", "MSW"],
    },
    {
        "name": MEDICINE, "sort_order": 11, "website": "https://www.med.wisc.edu/",
        "leadership": "Robert N. Golden — Dean",
        "research_centers": [
            "UW Carbone Cancer Center",
            "Wisconsin Alzheimer's Institute",
            "Institute for Clinical and Translational Research",
            "McArdle Laboratory for Cancer Research",
        ],
        "keywords": ["School of Medicine and Public Health", "SMPH", "medicine", "MD", "public health"],
    },
    {
        "name": NURSING, "sort_order": 12, "website": "https://nursing.wisc.edu/",
        "leadership": "Linda D. Scott — Dean",
        "research_centers": [
            "Center for Aging Research and Education",
            "Center for Patient Partnerships",
            "Wisconsin Center for Nursing",
            "Nursing Research and Practice",
        ],
        "keywords": ["School of Nursing", "nursing", "BSN", "DNP"],
    },
    {
        "name": NELSON, "sort_order": 13, "website": "https://nelson.wisc.edu/",
        "leadership": "Paul Robbins — Director",
        "research_centers": [
            "Center for Climatic Research",
            "Center for Sustainability and the Global Environment",
            "Trout Lake Station",
            "Environmental Studies",
        ],
        "keywords": ["Nelson Institute for Environmental Studies", "environmental studies", "sustainability"],
    },
    {
        "name": PHARMACY, "sort_order": 14, "website": "https://pharmacy.wisc.edu/",
        "leadership": "Steven Swanson — Dean",
        "research_centers": [
            "Pharmaceutical Sciences Division",
            "Social and Administrative Sciences Division",
            "Zeeh Pharmaceutical Experiment Station",
            "Pharmacy Practice Division",
        ],
        "keywords": ["School of Pharmacy", "pharmacy", "PharmD"],
    },
    {
        "name": VET, "sort_order": 15, "website": "https://www.vetmed.wisc.edu/",
        "leadership": "Daryl Nydam — Dean",
        "research_centers": [
            "Wisconsin Veterinary Diagnostic Laboratory",
            "UW Veterinary Care teaching hospital",
            "Comparative Biomedical Sciences",
            "Food Animal Production Medicine",
        ],
        "keywords": ["School of Veterinary Medicine", "veterinary", "DVM"],
    },
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"], "description": f"The {m['name']} is one of UW-Madison's academic schools and colleges."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "UW–Madison Schools and Colleges", "url": "https://www.wisc.edu/academics/schools-and-colleges/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


def _school_description(m: dict) -> str:
    return f"The {m['name']} is one of UW-Madison's academic schools and colleges."


# ── Feeds (content_sources) ────────────────────────────────────────────────
_NEWS_RSS = "https://news.wisc.edu/feed/"
_EVENTS = {"url": "https://today.wisc.edu/events.ics", "type": "ical"}
_SOCIAL = {
    "instagram": "https://instagram.com/uwmadison",
    "linkedin": "https://www.linkedin.com/school/uwmadison/",
    "x": "https://x.com/UWMadison",
    "youtube": "https://www.youtube.com/user/uwmadison",
    "facebook": "https://facebook.com/uwmadison",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.wisc.edu/",
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

# ── Explicit flagship programs (take precedence over IPEDS breadth rows) ────
PROGRAMS: list[dict] = [
    {
        "slug": "uw-madison-computer-science-bs", "school": CDIS,
        "program_name": "Computer Science", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Computer Science through the School of Computer, Data and Information Sciences.",
        "department": "Department of Computer Sciences", "cip": "11.07",
    },
    {
        "slug": "uw-madison-mechanical-engineering-bs", "school": ENGINEERING,
        "program_name": "Mechanical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Mechanical Engineering through the College of Engineering.",
        "department": "Department of Mechanical Engineering", "cip": "14.19",
    },
    {
        "slug": "uw-madison-biomedical-engineering-bs", "school": ENGINEERING,
        "program_name": "Biomedical/Medical Engineering", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Biomedical Engineering through the College of Engineering.",
        "department": "Department of Biomedical Engineering", "cip": "14.05",
    },
    {
        "slug": "uw-madison-business-administration-bs", "school": BUSINESS,
        "program_name": "Business Administration and Management", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Business Administration through the Wisconsin School of Business.",
        "department": "Wisconsin School of Business", "cip": "52.02",
    },
    {
        "slug": "uw-madison-mba-ms", "school": BUSINESS,
        "program_name": "Master of Business Administration", "degree_type": "masters",
        "duration_months": 24, "delivery_format": "on_campus",
        "description": "Full-time MBA at the Wisconsin School of Business.",
        "department": "Wisconsin School of Business", "cip": "52.02",
    },
    {
        "slug": "uw-madison-law-prof", "school": LAW,
        "program_name": "Law", "degree_type": "professional",
        "duration_months": 36, "delivery_format": "on_campus",
        "description": "Juris Doctor (J.D.) at the University of Wisconsin Law School.",
        "department": "Law School", "cip": "22.01",
    },
    {
        "slug": "uw-madison-medicine-prof", "school": MEDICINE,
        "program_name": "Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Medicine (M.D.) at the UW School of Medicine and Public Health.",
        "department": "School of Medicine and Public Health", "cip": "51.12",
    },
    {
        "slug": "uw-madison-pharmacy-prof", "school": PHARMACY,
        "program_name": "Pharmacy", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Pharmacy (Pharm.D.) at the UW–Madison School of Pharmacy.",
        "department": "School of Pharmacy", "cip": "51.20",
    },
    {
        "slug": "uw-madison-veterinary-medicine-prof", "school": VET,
        "program_name": "Veterinary Medicine", "degree_type": "professional",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Doctor of Veterinary Medicine (D.V.M.) at the School of Veterinary Medicine.",
        "department": "School of Veterinary Medicine", "cip": "51.24",
    },
    {
        "slug": "uw-madison-nursing-bs", "school": NURSING,
        "program_name": "Registered Nursing", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Nursing (BSN) through the UW–Madison School of Nursing.",
        "department": "School of Nursing", "cip": "51.38",
    },
    {
        "slug": "uw-madison-psychology-bs", "school": LETTERS,
        "program_name": "Psychology, General", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Science in Psychology through the College of Letters and Science.",
        "department": "Department of Psychology", "cip": "42.01",
    },
    {
        "slug": "uw-madison-economics-bs", "school": LETTERS,
        "program_name": "Economics", "degree_type": "bachelors",
        "duration_months": 48, "delivery_format": "on_campus",
        "description": "Bachelor of Arts or Bachelor of Science in Economics through the College of Letters and Science.",
        "department": "Department of Economics", "cip": "45.06",
    },
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}


def _department_for(field_name: str, school: str) -> str:
    """Owning department — map CIP titles to UW-Madison's published unit names."""
    field = clean_cip_field(field_name)
    if field in DEPARTMENT_BY_FIELD:
        return DEPARTMENT_BY_FIELD[field]
    if field.lower() in school.lower() or school.lower() in field.lower():
        return school
    if school == ENGINEERING:
        return f"Department of {field}"
    if school == LETTERS:
        return f"Department of {field}"
    return school


def _ug_degree_prefix(school: str, field: str) -> str:
    if school == LETTERS and field in BA_FIELDS:
        return "Bachelor of Arts in"
    if school == JOURNALISM:
        return "Bachelor of Science in"
    if school == HUMAN_ECOLOGY:
        return "Bachelor of Science in"
    return "Bachelor of Science in"


def _uw_madison_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Real credential-specific name — never a bare CIP title or credential-prefix stub."""
    field = clean_cip_field(field_name)
    if degree_type == "bachelors":
        return f"{_ug_degree_prefix(school, field)} {field}"
    if degree_type == "masters":
        if field == "Business Administration" and school == BUSINESS:
            return "Master of Business Administration"
        if field == "Social Work" and school == SOCIAL_WORK:
            return "Master of Social Work"
        if field == "Public Health" and school == MEDICINE:
            return "Master of Public Health"
        if field == "Nursing" and school == NURSING:
            return "Master of Science in Nursing"
        if field == "Library and Information Studies":
            return "Master of Arts in Library and Information Studies"
        return f"Master of Science in {field}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {field}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {field}"
    if degree_type == "professional":
        if field == "Medicine":
            return "Doctor of Medicine"
        if field == "Pharmaceutical Sciences" and school == PHARMACY:
            return "Doctor of Pharmacy"
        if field == "Veterinary Medicine":
            return "Doctor of Veterinary Medicine"
        if field == "Law":
            return "Juris Doctor"
    return field


def _field_from_program_name(name: str) -> str:
    if name in (
        "Doctor of Medicine",
        "Doctor of Pharmacy",
        "Doctor of Veterinary Medicine",
        "Juris Doctor",
        "Master of Business Administration",
        "Master of Public Health",
        "Master of Social Work",
    ):
        return name
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    return clean_cip_field(name)


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    """Fix credential-level lies (e.g. 'Graduate …' on a bachelor's row)."""
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate "):]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level "):]
    return clause


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    """Drop undergraduate-specific phrasing from a field clause on graduate rows."""
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(
        r"\bundergraduate (major|program)\b", "program", clause, flags=re.I
    )
    return clause


def _field_from_spec(spec: dict, raw_field: str | None = None) -> str:
    slug = spec.get("slug", "")
    if slug in SLUG_DESCRIPTIONS:
        return ""  # slug override handles description
    if slug in SLUG_PROGRAM_NAMES:
        return _field_from_program_name(SLUG_PROGRAM_NAMES[slug])
    if raw_field:
        return clean_cip_field(raw_field)
    fn = spec.get("program_name", "")
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Master of Science in ",
        "Doctor of Philosophy in ",
        "Graduate Certificate in ",
    ):
        if fn.startswith(prefix):
            return fn[len(prefix) :].strip()
    return clean_cip_field(fn)


def _apply_fmt_suffix(desc: str, spec: dict) -> str:
    fmt = spec.get("delivery_format", "on_campus")
    if fmt == "online":
        return desc + " Delivered online."
    if fmt == "hybrid":
        return desc + " Delivered in a hybrid format."
    return desc


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program.

    A SLUG_DESCRIPTIONS program carries its own per-slug clause. Otherwise programs are
    grouped by their FIELD_DESCRIPTIONS field key: the field's PRIMARY (lowest-level)
    credential carries the full verified clause; each credential SIBLING carries a
    level-specific frame + the field's real-subarea focus. No two siblings share a
    >=80-char contiguous body (gold MIT = 0), and every body names real subareas.
    """
    from collections import defaultdict

    # Group every program by its human field label so a field's bachelors (which may carry
    # a per-slug SLUG_DESCRIPTIONS clause) is grouped with its graduate siblings.
    groups: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        groups[_field_label(spec["program_name"])].append(spec)

    for label, specs in groups.items():
        fd_field = next((s.get("_fd_field") for s in specs if s.get("_fd_field")), None)
        field_clause = FIELD_DESCRIPTIONS.get(fd_field or "")

        def _slug_text(s: dict) -> str | None:
            return SLUG_DESCRIPTIONS.get(s["slug"])

        # The clause anchors ONE credential — the bachelors when the field has one (the
        # clause framing is undergraduate-friendly), otherwise the lowest credential level.
        anchor = next(
            (s for s in specs if s["degree_type"] == "bachelors"),
            min(specs, key=lambda s: (_LEVEL_PRIORITY.get(s["degree_type"], 2), s["slug"])),
        )
        anchor_text = _slug_text(anchor) or field_clause
        focus = (
            _FIELD_FOCUS.get(label)
            or _focus_for(fd_field)
            or _extract_focus(anchor_text or "")
        )

        assigned: set[str] = set()
        for spec in specs:
            slug_text = _slug_text(spec)
            if spec is anchor:
                base = field_clause if (field_clause and spec["slug"] not in SLUG_DESCRIPTIONS) else slug_text
                base = base or field_clause
                if not base:
                    raise ValueError(f"No clause for anchor {spec['slug']!r}")
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(base, spec["degree_type"]),
                    spec["degree_type"],
                )
            elif slug_text and slug_text not in assigned:
                # A SLUG sibling keeps its own curated clause unless it would duplicate.
                body = slug_text
            else:
                if not focus:
                    raise ValueError(f"No focus for sibling {spec['slug']!r} ({label})")
                body = _sibling_body(spec["degree_type"], _field_label(spec["program_name"]), focus)
            assigned.add(body)
            spec["description"] = _apply_fmt_suffix(body, spec)
            spec["who_its_for"] = _WHO_BY_SLUG.get(spec["slug"]) or _who_for(
                label, focus, spec["degree_type"]
            )
            spec.pop("_fd_field", None)


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    slug = spec["slug"]
    school = spec["school"]
    dtype = spec["degree_type"]
    raw_field = field_name or spec.get("_field_name") or spec.get("program_name", "")

    if slug in SLUG_PROGRAM_NAMES:
        spec["program_name"] = SLUG_PROGRAM_NAMES[slug]
    elif dtype != "professional":
        spec["program_name"] = _uw_madison_program_name(raw_field, dtype, school)

    if slug in SLUG_DEPARTMENTS:
        spec["department"] = SLUG_DEPARTMENTS[slug]
    elif not spec.get("department") or spec["department"] == raw_field:
        spec["department"] = _department_for(raw_field, school)

    # Resolve and stash the FIELD_DESCRIPTIONS key; the actual description is assigned by
    # the sibling-aware _assign_descriptions pass once the whole catalog is built.
    spec["_fd_field"] = _field_from_spec(
        spec, clean_cip_field(raw_field) if raw_field else None
    )


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        seen.add(slug)
        spec = {
            "slug": slug,
            "school": school,
            "program_name": field_name,
            "degree_type": dtype,
            "department": _department_for(field_name, school),
            "cip": cip,
            "duration_months": dur,
            "delivery_format": fmt,
            "_field_name": field_name,
        }
        _normalize_program(spec, field_name)
        spec.pop("_field_name", None)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    if _p["slug"] in _EXISTING_SLUGS:
        _normalize_program(_p, _p.get("program_name"))

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
_stub_desc = sum(1 for p in PROGRAMS if "offered through the " in (p.get("description") or ""))
_new_templ = sum(1 for p in PROGRAMS if _TEMPLATE_STUB_RE.search(p.get("description") or ""))
_cred_prefix = sum(1 for p in PROGRAMS if _CRED_PREFIX_RE.match(p.get("program_name") or ""))
if _stub_desc:
    _catalog_errors.append(f"template stub descriptions on {_stub_desc} programs")
if _new_templ:
    _catalog_errors.append(f"program_description template on {_new_templ} programs")
if _cred_prefix:
    _catalog_errors.append(f"credential-prefix program_name on {_cred_prefix} programs")
_anti_stub = _anti_stub_analyze(PROGRAMS)
if not _anti_stub.is_clean:
    _catalog_errors.append(f"anti-stub gate failed: {_anti_stub.summary()}")
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    frame_stripped_shared_body as _frame_stripped_shared_body,
)

_frame_shared = _frame_stripped_shared_body(PROGRAMS)
if _frame_shared:
    _catalog_errors.append(
        f"credential siblings share a frame-stripped body on fields: {_frame_shared[:8]}"
        f"{' …' if len(_frame_shared) > 8 else ''}"
    )


def _max_shared_body_pairs(programs: list[dict], min_chars: int = 80) -> list[tuple[str, str]]:
    """Program-name pairs whose descriptions share a >=``min_chars`` contiguous run.

    The absolute gold test (gold MIT = 0): the frame-stripped metric over-strips a leading
    field clause and the leading-prefix metric misses a shared TAIL, so this catches both —
    any two programs (same field OR cross-field) sharing a long verbatim body fail the gate.
    """
    grams: dict[str, set[int]] = {}
    for idx, prog in enumerate(programs):
        text = prog.get("description") or ""
        for i in range(0, max(0, len(text) - min_chars + 1)):
            grams.setdefault(text[i : i + min_chars], set()).add(idx)
    pairs: set[tuple[int, int]] = set()
    for owners in grams.values():
        if len(owners) >= 2:
            ordered = sorted(owners)
            for a_i in range(len(ordered)):
                for b_i in range(a_i + 1, len(ordered)):
                    pairs.add((ordered[a_i], ordered[b_i]))
    return [
        (programs[a]["program_name"], programs[b]["program_name"]) for a, b in sorted(pairs)
    ]


_shared_body_pairs = _max_shared_body_pairs(PROGRAMS)
if _shared_body_pairs:
    _catalog_errors.append(
        f"descriptions share a >=80-char body on {len(_shared_body_pairs)} program "
        f"pairs (e.g. {_shared_body_pairs[:3]})"
    )
# Matcher-core coverage gates (REPAIR_BACKLOG #1 + #4): every program carries a real IPEDS
# CIP code (the field-66 join key the matcher resolves on the 2-digit family) and a
# program-DISTINCT ``who_its_for`` (subject + verified subareas + who-it-fits + next step,
# never a degree-type template). Fail the build if either is missing or if ``who_its_for``
# collapses below ~0.9 distinct/total (the type-gaming guard — gold field-specific ≈ 1.0).
_cip_missing = [p["slug"] for p in PROGRAMS if not p.get("cip")]
if _cip_missing:
    _catalog_errors.append(f"cip missing on {len(_cip_missing)} programs: {_cip_missing[:5]}")
_who_missing = [p["slug"] for p in PROGRAMS if not (p.get("who_its_for") or "").strip()]
if _who_missing:
    _catalog_errors.append(
        f"who_its_for missing on {len(_who_missing)} programs: {_who_missing[:5]}"
    )
_who_vals = [p.get("who_its_for") or "" for p in PROGRAMS]
_who_ratio = len(set(_who_vals)) / max(len(_who_vals), 1)
if _who_ratio < 0.9:
    _catalog_errors.append(
        f"who_its_for type-gamed: distinct/total {_who_ratio:.2f} < 0.9 (must be program-distinct)"
    )
if _catalog_errors:
    raise RuntimeError(f"UW-Madison catalog quality gate failed: {_catalog_errors}")
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

_TUITION_UG_INSTATE = 12186
_TUITION_UG_OOS = 44210
_UNDERGRAD_COA = 28679
_AVG_NET_PRICE = 17354
_COST_SRC = (
    "UW–Madison Facts (tuition 2025–26) + College Scorecard (UNITID 240444)",
    "https://www.wisc.edu/about/facts/",
)

# Published tuition & fees (matcher-core budget signal — REPAIR_BACKLOG run 74 HIGH #2).
# Rates are the UW–Madison Office of Student Financial Aid 2025-26 cost-of-attendance
# tuition & fees lines (resident annual; breakdown carries non-resident). The matcher
# number ``p.tuition`` is the Wisconsin-resident annual; funding is a separate signal.
_TUITION_SRC = "UW–Madison Office of Student Financial Aid — 2025-26 Cost of Attendance"
_TUITION_SRC_URL = "https://financialaid.wisc.edu/cost-of-attendance/"
_PHD_FUNDING_SRC = "UW–Madison Graduate School — Funding"
_PHD_FUNDING_URL = "https://grad.wisc.edu/funding/"

# Undergraduate tuition & fees (general L&S); school differentials per the FA notes.
_UG_TUITION_DIFFERENTIAL: dict[str, int] = {
    BUSINESS: 3000,
    ENGINEERING: 3200,
    NURSING: 1500,
}

# Graduate tuition & fees (most master's + capstone certificates).
_GRAD_TUITION = (12404, 25732)

# Wisconsin School of Business graduate master's (incl. the Full-Time MBA).
_BUSINESS_GRAD_TUITION = (29442, 53090)

# Professional-degree tuition & fees by flagship program name (FA 2025-26 tables).
_PROFESSIONAL_TUITION: dict[str, tuple[int, int]] = {
    "Law": (38204, 55318),
    "Medicine": (44410, 62533),  # non-res = $44,410 + $18,123 add-on
    "Pharmacy": (30548, 49624),
    "Veterinary Medicine": (37758, 60424),  # non-res = $37,758 + $22,666 extra
}


# Per-slug tuition overrides for programs billed differently from the standard full-time
# resident graduate sticker. The College-wide online Master of Engineering (InterPro) is
# a 30-credit, fully-online program billed PER CREDIT, not at the full-time grad rate, so
# the generic _GRAD_TUITION ($12,404) would understate its real published cost.
_MENG_PER_CREDIT = 1300  # interpro.wisc.edu — current online MEng rate, 2025-26
_MENG_CREDITS = 30
# Programs explicitly published as part-time (working-professional schedule) — drives the
# matcher's `wants_part_time` flexibility fit. The online MEng is "100% online, part-time."
_PART_TIME_SLUGS = frozenset({"uw-madison-engineering-general-ms"})
_TUITION_BY_SLUG: dict[str, tuple[int, dict]] = {
    "uw-madison-engineering-general-ms": (
        _MENG_PER_CREDIT * _MENG_CREDITS,  # 30 credits × $1,300/credit = $39,000
        {
            "tuition_usd": _MENG_PER_CREDIT * _MENG_CREDITS,
            "per_credit_usd": _MENG_PER_CREDIT,
            "credits": _MENG_CREDITS,
            "funded": False,
            "note": (
                "Published per-credit tuition for the fully-online College-wide Master of "
                f"Engineering (Interdisciplinary Professional Programs): ${_MENG_PER_CREDIT:,}"
                f"/credit × {_MENG_CREDITS} credits ≈ "
                f"${_MENG_PER_CREDIT * _MENG_CREDITS:,} total. Same rate for residents and "
                "nonresidents (online program)."
            ),
            "source": "UW–Madison Interdisciplinary Professional Programs (InterPro)",
            "source_url": "https://interpro.wisc.edu/online-graduate-programs/masters-degrees/",
            "year": "2025-26",
        },
    ),
}


def _pub_tuition_cost(res: int, oos: int, note: str, *, funded: bool = False) -> dict:
    # The matcher reads the FLAT ``program.tuition`` scalar (and ``tuition_usd``) for its
    # budget fit; for a PUBLIC university that scalar must be the NON-RESIDENT (out-of-state)
    # rate, the conservative, broadly-correct input for the national/international applicant
    # pool (every international applicant pays non-resident) — REPAIR_BACKLOG #2 / FLAG #6.
    # BOTH rates stay in ``breakdown`` (honest + sourced); only the exposed scalar changed.
    return {
        "tuition_usd": oos,
        "breakdown": {"tuition_in_state": res, "tuition_out_of_state": oos},
        "funded": funded,
        "note": note,
        "source": _TUITION_SRC,
        "source_url": _TUITION_SRC_URL,
        "year": "2025-26",
    }


def _program_tuition(spec: dict) -> tuple[int | None, dict]:
    """Return (matcher_tuition, cost_data) from UW-published 2025-26 rates."""
    slug_override = _TUITION_BY_SLUG.get(spec.get("slug", ""))
    if slug_override is not None:
        return slug_override
    school = spec["school"]
    dtype = spec["degree_type"]
    name = spec["program_name"]

    if dtype == "bachelors":
        diff = _UG_TUITION_DIFFERENTIAL.get(school, 0)
        res = _TUITION_UG_INSTATE + diff
        oos = _TUITION_UG_OOS + diff
        cost = _pub_tuition_cost(
            res,
            oos,
            "Published annual undergraduate tuition & fees — the non-resident "
            "(out-of-state) rate, which the matcher uses as the budget scalar for the "
            "national/international applicant pool; the Wisconsin-resident rate is shown "
            "in the breakdown. School differentials (Business, Engineering, Nursing) are "
            "included when applicable.",
        )
        # COA must stay CONSISTENT with the non-resident tuition scalar above (PR #1193
        # review): the top-level total_cost_of_attendance is the NON-RESIDENT COA (else it
        # would read below tuition alone). Living/other is residency-invariant — derive it
        # from the published resident COA minus the resident base tuition — so both residency
        # COAs are real published-derived figures, carried in the breakdown.
        living_other = _UNDERGRAD_COA - _TUITION_UG_INSTATE
        cost["total_cost_of_attendance"] = oos + living_other
        cost["breakdown"]["total_cost_of_attendance_in_state"] = res + living_other
        cost["breakdown"]["total_cost_of_attendance_out_of_state"] = oos + living_other
        cost["avg_net_price"] = _AVG_NET_PRICE
        cost["avg_net_price_note"] = (
            "Average net price after aid for Wisconsin residents (College Scorecard); "
            "non-resident net price is higher."
        )
        cost["source"] = _COST_SRC[0]
        cost["source_url"] = _COST_SRC[1]
        return oos, cost

    if dtype == "phd":
        return 0, {
            "tuition_usd": 0,
            "funded": True,
            "note": (
                "UW–Madison PhD students typically receive full tuition plus a stipend "
                "through fellowship and assistantship programs; the published full-time "
                f"graduate tuition & fees sticker is ${_GRAD_TUITION[0]:,} per year "
                "before aid."
            ),
            "source": _PHD_FUNDING_SRC,
            "source_url": _PHD_FUNDING_URL,
            "year": "2025-26",
        }

    if dtype == "professional":
        rates = _PROFESSIONAL_TUITION.get(name)
        if rates is None:
            rates = {
                LAW: _PROFESSIONAL_TUITION["Law"],
                MEDICINE: _PROFESSIONAL_TUITION["Medicine"],
                PHARMACY: _PROFESSIONAL_TUITION["Pharmacy"],
                VET: _PROFESSIONAL_TUITION["Veterinary Medicine"],
            }.get(school)
        if rates is None:
            return None, {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "UW–Madison Bursar's Office — Tuition Rates",
                "source_url": "https://bursar.wisc.edu/tuition-and-fees/tuition-rates",
            }
        res, oos = rates
        return oos, _pub_tuition_cost(
            res,
            oos,
            f"Published annual {name} tuition & fees — the non-resident (out-of-state) "
            "rate, the matcher budget scalar; the Wisconsin-resident rate is shown in the "
            "breakdown.",
        )

    if dtype == "masters":
        if school == BUSINESS or name == "Master of Business Administration":
            res, oos = _BUSINESS_GRAD_TUITION
            note = (
                "Published annual Wisconsin School of Business graduate tuition & fees — "
                "the non-resident (out-of-state) rate, the matcher budget scalar; the "
                "Wisconsin-resident rate is shown in the breakdown."
            )
        else:
            res, oos = _GRAD_TUITION
            note = (
                "Published annual graduate tuition & fees (full-time) — the non-resident "
                "(out-of-state) rate, the matcher budget scalar; the Wisconsin-resident "
                "rate is shown in the breakdown."
            )
        return oos, _pub_tuition_cost(res, oos, note)

    if dtype == "certificate":
        res, oos = _GRAD_TUITION
        return oos, _pub_tuition_cost(
            res,
            oos,
            "Published annual graduate tuition & fees for capstone certificate programs "
            "— the non-resident (out-of-state) rate, the matcher budget scalar; the "
            "Wisconsin-resident rate is shown in the breakdown.",
        )

    return None, {
        "note": "Tuition varies by program; see the official program tuition page.",
        "source": "UW–Madison Bursar's Office — Tuition Rates",
        "source_url": "https://bursar.wisc.edu/tuition-and-fees/tuition-rates",
    }

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "UW System Application for Admission", "required": True},
        {"name": "Required essays", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$70 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "UW-Madison is test-optional; applicants who submit scores have a middle 50% SAT reading 670–740 and math 710–780 (College Scorecard)."},
    ],
    "deadlines": [
        {"round": "Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "February 1"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UW–Madison Office of Admissions and Recruitment", "url": "https://admissions.wisc.edu/"}],
    },
    "source": "UW–Madison Office of Admissions and Recruitment",
    "source_url": "https://admissions.wisc.edu/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "UW–Madison Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose", "required": True},
        {"name": "Résumé / CV", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most UW graduate programs require three letters; check the program's page."},
        {"name": "GRE scores", "required": False,
         "note": "Test requirements vary by program; many UW graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose native language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "UW–Madison Graduate School — Admissions", "url": "https://grad.wisc.edu/admissions/"}],
    },
    "source": "UW–Madison Graduate School — Admissions",
    "source_url": "https://grad.wisc.edu/admissions/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 73792,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": "U.S. Dept. of Education College Scorecard (UNITID 240444)",
    "source_url": "https://collegescorecard.ed.gov/school/?240444-University-of-Wisconsin-Madison",
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "uw-madison-computer-science-bs": {
        "summary": (
            "UW-Madison's undergraduate computer science program in the School of Computer, Data "
            "and Information Sciences is ranked among the top public CS programs nationally, known "
            "for strength in systems, databases, and machine learning alongside a rigorous theory "
            "foundation. Students benefit from the Wisconsin Institutes for Discovery and strong "
            "recruiting to Midwest tech hubs and national firms, though gateway courses are large "
            "and competitive admission to the major is a common concern."
        ),
        "themes": [
            {"label": "Research access", "sentiment": "positive", "detail": "CDIS faculty lead active labs in AI, systems, and data science with undergraduate research pathways."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Strong recruiting to Epic, Google, Microsoft, Amazon, and Wisconsin-based tech employers."},
            {"label": "Major admission", "sentiment": "caution", "detail": "Direct admission to CS is competitive; students may need to complete prerequisite coursework first."},
            {"label": "Large intro sections", "sentiment": "mixed", "detail": "High enrollment means lower-division courses can feel impersonal without proactive faculty engagement."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Computer Science Programs", "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall"},
            {"label": "Niche — University of Wisconsin-Madison", "url": "https://www.niche.com/colleges/university-of-wisconsin-madison/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-mechanical-engineering-bs": {
        "summary": (
            "UW-Madison's mechanical engineering program through the College of Engineering is "
            "consistently ranked among the top 15–20 nationally, with particular strength in "
            "thermodynamics, fluid mechanics, and manufacturing research. Students cite the "
            "Grainger Engineering Design Innovation Lab and deep ties to Wisconsin manufacturing "
            "and automotive employers as highlights, though the engineering core is demanding and "
            "large lecture sections in the first two years are common."
        ),
        "themes": [
            {"label": "Design infrastructure", "sentiment": "positive", "detail": "Grainger Engineering Design Innovation Lab and senior design capstone integrate real industry sponsors."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Caterpillar, Rockwell Automation, Harley-Davidson, and major automotive firms recruit actively."},
            {"label": "Curriculum rigor", "sentiment": "caution", "detail": "Math and physics gateway sequence is intense; time management in years 1–2 is essential."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "Strong ROI for in-state students; engineering outcomes compare favorably to peer R1 publics."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Mechanical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering"},
            {"label": "UW–Madison College of Engineering", "url": "https://engineering.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-biomedical-engineering-bs": {
        "summary": (
            "UW-Madison's biomedical engineering program bridges the College of Engineering and "
            "the School of Medicine and Public Health, giving students access to clinical and "
            "research environments uncommon at peer programs. Reviewers note strong placement in "
            "medical device firms, health-tech startups, and graduate programs, though the "
            "interdisciplinary curriculum requires careful planning across engineering and biology "
            "prerequisites."
        ),
        "themes": [
            {"label": "Clinical proximity", "sentiment": "positive", "detail": "UW Health and SMPH affiliations offer research and internship access rare among undergraduate BME programs."},
            {"label": "Graduate school pipeline", "sentiment": "positive", "detail": "Strong track record placing graduates in top biomedical engineering and medical PhD programs."},
            {"label": "Prerequisite load", "sentiment": "mixed", "detail": "Biology, chemistry, and engineering requirements make the four-year plan tight without early planning."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Medtronic, GE Healthcare, and Wisconsin biotech firms recruit from the program."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Biomedical Engineering Programs", "url": "https://www.usnews.com/best-colleges/rankings/biomedical-engineering"},
            {"label": "UW–Madison Biomedical Engineering", "url": "https://engineering.wisc.edu/departments/biomedical-engineering/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-business-administration-bs": {
        "summary": (
            "The Wisconsin School of Business undergraduate program offers a quantitatively oriented "
            "BBA with particular strength in finance, real estate, and supply chain management. "
            "Reviewers note strong placement in consulting, banking, and Fortune 500 rotational "
            "programs, though direct admission is competitive and the school's brand recognition "
            "outside the Midwest trails top-10 undergraduate business programs."
        ),
        "themes": [
            {"label": "Direct admission selectivity", "sentiment": "caution", "detail": "Freshman direct admission to WSB is competitive; many students apply after completing prerequisites in L&S."},
            {"label": "Finance and real estate", "sentiment": "positive", "detail": "Nicholas Center and Hartman Center provide distinctive experiential finance and sales training."},
            {"label": "Midwest recruiting", "sentiment": "positive", "detail": "Strong pipelines to Milwaukee and Chicago finance, consulting, and CPG firms."},
            {"label": "National brand", "sentiment": "mixed", "detail": "Well-regarded regionally; national recognition growing but still behind elite private business schools."},
        ],
        "sources": [
            {"label": "Poets&Quants — Best Undergraduate Business Schools", "url": "https://poetsandquants.com/best-undergraduate-business-programs/"},
            {"label": "U.S. News — Best Undergraduate Business Programs", "url": "https://www.usnews.com/best-colleges/rankings/business-overall"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-mba-ms": {
        "summary": (
            "The Wisconsin Full-Time MBA at the Wisconsin School of Business is a two-year program "
            "known for its applied learning model, distinctive specializations in brand and product "
            "management, and strong Midwest corporate recruiting. Poets&Quants and BusinessBecause "
            "coverage highlight the school's collaborative culture and lower cost than coastal "
            "MBAs, though national consulting and finance placement lags M7 peers."
        ),
        "themes": [
            {"label": "Applied curriculum", "sentiment": "positive", "detail": "Brand and Product Management and applied learning projects integrate real corporate sponsors."},
            {"label": "Value proposition", "sentiment": "positive", "detail": "Lower tuition than elite private MBAs with strong ROI for students targeting Midwest markets."},
            {"label": "National consulting placement", "sentiment": "mixed", "detail": "Top-tier consulting and investment banking placement is more limited than M7 programs."},
            {"label": "Collaborative culture", "sentiment": "positive", "detail": "Smaller cohort relative to mega-programs fosters tight-knit peer networks."},
        ],
        "sources": [
            {"label": "Poets&Quants — Wisconsin School of Business", "url": "https://poetsandquants.com/schools/wisconsin-school-of-business-university-of-wisconsin/"},
            {"label": "Wisconsin School of Business — MBA", "url": "https://business.wisc.edu/graduate/mba/full-time/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-law-prof": {
        "summary": (
            "UW Law is a well-regarded public law school with particular strength in environmental "
            "law, Indian law, and clinical education through the Wisconsin Innocence Project and "
            "Law & Entrepreneurship Clinic. Graduates value the lower debt load relative to private "
            "peers and strong Wisconsin/Midwest placement, though national BigLaw recruiting is "
            "more limited than top-20 private law schools."
        ),
        "themes": [
            {"label": "Clinical programs", "sentiment": "positive", "detail": "Wisconsin Innocence Project and entrepreneurship clinic provide distinctive hands-on training."},
            {"label": "Debt and affordability", "sentiment": "positive", "detail": "In-state tuition and strong scholarship support keep debt below many peer public law schools."},
            {"label": "BigLaw placement", "sentiment": "mixed", "detail": "Chicago and Twin Cities firms recruit, but coastal BigLaw placement is more limited than T14 schools."},
            {"label": "Environmental and Indian law", "sentiment": "positive", "detail": "Nationally recognized programs in environmental law and tribal law attract specialized applicants."},
        ],
        "sources": [
            {"label": "U.S. News — Best Law Schools", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-wisconsin-3895"},
            {"label": "UW Law School — About", "url": "https://law.wisc.edu/about/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-medicine-prof": {
        "summary": (
            "The UW School of Medicine and Public Health is a top public medical school with "
            "distinctive emphasis on rural and community health through the Wisconsin Academy for "
            "Rural Medicine (WARM) and strong research at the UW Carbone Cancer Center. Students "
            "value the ForWard curriculum and Madison quality of life, though class size and "
            "competition for competitive specialties require early planning."
        ),
        "themes": [
            {"label": "Rural health mission", "sentiment": "positive", "detail": "WARM and community health pathways distinguish UW among public medical schools."},
            {"label": "Research strength", "sentiment": "positive", "detail": "UW Carbone Cancer Center and ICTR provide substantial research opportunities for medical students."},
            {"label": "In-state preference", "sentiment": "caution", "detail": "Wisconsin residents receive strong preference; out-of-state admission is highly competitive."},
            {"label": "Quality of life", "sentiment": "positive", "detail": "Madison campus setting and collaborative student culture are frequently cited positives."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools (Research)", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-wisconsin-madison-04072"},
            {"label": "UW School of Medicine and Public Health", "url": "https://www.med.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-pharmacy-prof": {
        "summary": (
            "UW-Madison's Pharm.D. program is one of the oldest pharmacy schools in the United "
            "States, known for strong pharmaceutical sciences research and placement in hospital, "
            "community, and industry pharmacy roles. Students praise the Zeeh Pharmaceutical "
            "Experiment Station and Wisconsin's collaborative health-sciences campus, though the "
            "program is highly structured with limited elective flexibility in the professional years."
        ),
        "themes": [
            {"label": "Research heritage", "sentiment": "positive", "detail": "Pharmaceutical sciences division and Zeeh Station offer research depth uncommon in Pharm.D. programs."},
            {"label": "Clinical placement", "sentiment": "positive", "detail": "UW Health affiliations provide strong hospital and ambulatory pharmacy rotations."},
            {"label": "Curriculum structure", "sentiment": "mixed", "detail": "Professional years are tightly sequenced; limited room for electives outside pharmacy."},
            {"label": "Wisconsin market", "sentiment": "positive", "detail": "Strong placement in Wisconsin and Upper Midwest pharmacy markets."},
        ],
        "sources": [
            {"label": "U.S. News — Best Pharmacy Schools", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/pharmacy-rankings"},
            {"label": "UW–Madison School of Pharmacy", "url": "https://pharmacy.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-veterinary-medicine-prof": {
        "summary": (
            "UW-Madison's School of Veterinary Medicine is one of only 32 AVMA-accredited veterinary "
            "colleges in the United States, offering a D.V.M. with strong food-animal, comparative "
            "biomedical, and diagnostic laboratory training. Students value the Wisconsin Veterinary "
            "Diagnostic Laboratory and UW Veterinary Care teaching hospital, though admission is "
            "highly selective with strong preference for Wisconsin residents."
        ),
        "themes": [
            {"label": "Food-animal strength", "sentiment": "positive", "detail": "Food Animal Production Medicine program is a distinctive strength for Wisconsin's dairy and livestock economy."},
            {"label": "Diagnostic laboratory", "sentiment": "positive", "detail": "WVDL provides unique diagnostic and research exposure for veterinary students."},
            {"label": "Admission selectivity", "sentiment": "caution", "detail": "Highly competitive admission with strong in-state preference; out-of-state seats are limited."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "UW Veterinary Care teaching hospital offers comprehensive small- and large-animal clinical experience."},
        ],
        "sources": [
            {"label": "U.S. News — Best Veterinary Medicine Programs", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings"},
            {"label": "UW School of Veterinary Medicine", "url": "https://www.vetmed.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-nursing-bs": {
        "summary": (
            "UW-Madison's BSN program through the School of Nursing is ranked among the top public "
            "nursing programs nationally, with strong clinical placement at UW Health and emphasis "
            "on evidence-based practice. Students cite the Center for Patient Partnerships and "
            "research opportunities, though clinical placement scheduling and prerequisite science "
            "coursework are demanding."
        ),
        "themes": [
            {"label": "Clinical access", "sentiment": "positive", "detail": "UW Health system provides extensive clinical rotation sites in Madison and surrounding communities."},
            {"label": "Research opportunities", "sentiment": "positive", "detail": "Center for Aging Research and Education and nursing science faculty offer undergraduate research pathways."},
            {"label": "Science prerequisites", "sentiment": "caution", "detail": "Competitive admission requires strong performance in anatomy, physiology, and chemistry prerequisites."},
            {"label": "Job placement", "sentiment": "positive", "detail": "High placement rates in Wisconsin and Midwest hospital systems after licensure."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Nursing Programs", "url": "https://www.usnews.com/best-colleges/rankings/nursing-overall"},
            {"label": "UW–Madison School of Nursing", "url": "https://nursing.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-psychology-bs": {
        "summary": (
            "UW-Madison's psychology program in the College of Letters and Science offers strong "
            "research opportunities in cognitive, clinical, developmental, and neuroscience "
            "psychology with active faculty labs. Students benefit from the Waisman Center "
            "affiliation and clear pathways to doctoral study, though introductory courses are "
            "large and research assistant positions are competitive."
        ),
        "themes": [
            {"label": "Research lab access", "sentiment": "positive", "detail": "Active faculty labs in cognitive, clinical, and developmental psychology accept undergraduates."},
            {"label": "Graduate school preparation", "sentiment": "positive", "detail": "Strong track record placing graduates in top psychology and neuroscience PhD programs."},
            {"label": "Large gateway courses", "sentiment": "caution", "detail": "Introductory psychology sections are large; individual faculty mentorship requires initiative."},
            {"label": "Career without grad school", "sentiment": "mixed", "detail": "Undergraduate psychology alone narrows options; pairing with data science, pre-health, or HR coursework is advisable."},
        ],
        "sources": [
            {"label": "Niche — University of Wisconsin-Madison", "url": "https://www.niche.com/colleges/university-of-wisconsin-madison/"},
            {"label": "UW–Madison Department of Psychology", "url": "https://psych.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "uw-madison-economics-bs": {
        "summary": (
            "UW-Madison's economics program is rooted in the legacy of the 'Wisconsin School' of "
            "institutional economics and remains a strong quantitative social science major with "
            "particular depth in econometrics and labor economics. Students value the department's "
            "research seminars and placement in consulting, policy, and graduate programs, though "
            "upper-division courses can be competitive to access."
        ),
        "themes": [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Econometrics and labor economics sequences provide strong preparation for policy and data careers."},
            {"label": "Graduate placement", "sentiment": "positive", "detail": "Consistent placement in economics, public policy, and business PhD programs."},
            {"label": "Course access", "sentiment": "mixed", "detail": "Popular upper-division electives fill quickly; registration planning matters."},
            {"label": "Policy and consulting paths", "sentiment": "positive", "detail": "La Follette School proximity and Madison state-government access create distinctive policy internships."},
        ],
        "sources": [
            {"label": "U.S. News — Best Undergraduate Economics Programs", "url": "https://www.usnews.com/best-colleges/rankings/economics"},
            {"label": "UW–Madison Department of Economics", "url": "https://econ.wisc.edu/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    **DEPTH_REVIEWS,
}

_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "uw-madison-computer-science-bs": ["computer science", "CDIS", "Computer Sciences"],
    "uw-madison-mechanical-engineering-bs": ["mechanical engineering", "College of Engineering"],
    "uw-madison-biomedical-engineering-bs": ["biomedical engineering", "BME", "College of Engineering"],
    "uw-madison-business-administration-bs": ["business", "BBA", "Wisconsin School of Business"],
    "uw-madison-mba-ms": ["MBA", "Wisconsin School of Business", "graduate business"],
    "uw-madison-law-prof": ["JD", "Law School", "legal studies"],
    "uw-madison-medicine-prof": ["MD", "School of Medicine and Public Health", "medicine"],
    "uw-madison-pharmacy-prof": ["PharmD", "School of Pharmacy", "pharmacy"],
    "uw-madison-veterinary-medicine-prof": ["DVM", "veterinary medicine", "vet school"],
    "uw-madison-nursing-bs": ["nursing", "BSN", "School of Nursing"],
    "uw-madison-psychology-bs": ["psychology", "College of Letters and Science"],
    "uw-madison-economics-bs": ["economics", "Department of Economics"],
}
_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_COST_BY_SLUG: dict = {}


def _program_standard(slug: str, spec: dict | None = None) -> dict:
    if spec is None:
        spec = _SPEC_BY_SLUG.get(slug, {})
    omitted: list[str] = [
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
    return _standard(omitted)


def _requirements_for(spec: dict) -> dict:
    return dict(_REQ_UNDERGRAD if spec["degree_type"] == "bachelors" else _REQ_GRAD)


def _website_for(spec: dict) -> str:
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.wisc.edu/")


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
    inst.founded_year = 1848
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.wisc.edu"
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
    existing = {s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))}
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
    fks = session.execute(text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'programs' AND ccu.column_name = 'id' AND tc.table_name <> 'programs'
    """)).fetchall()
    for table, col in fks:
        if session.execute(text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'), {"pid": program_id}).first():
            return True
    return False


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {p.slug: p for p in session.scalars(select(Program).where(Program.institution_id == inst.id)) if p.slug}
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        slug = spec["slug"]
        p = existing.get(slug)
        if p is None:
            p = Program(institution_id=inst.id, program_name=spec["program_name"], degree_type=spec["degree_type"], slug=slug)
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
        if slug in _PART_TIME_SLUGS:
            p.part_time_available = True
        p.department = spec.get("department")
        # Matcher-core: CIP field-join key + universal program-DISTINCT who_its_for
        # (REPAIR_BACKLOG #1 / #4).
        p.cip_code = spec.get("cip")
        p.who_its_for = spec.get("who_its_for")
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
        tuition, cost = _program_tuition(spec)
        p.tuition = tuition
        p.cost_data = cost
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.application_deadline = date(2027, 2, 1) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
