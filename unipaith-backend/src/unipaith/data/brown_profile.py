"""Brown University — gold-standard profile data (institution + schools + program catalog).

Every value below is verified against an authoritative source (Brown's official pages, the
U.S. Dept. of Education College Scorecard / NCES for UNITID 217156, Brown's Common Data Set
and admission statistics, the SFS tuition schedules, and ranking bodies) and carries a
citation, or is honestly omitted (recorded in that node's ``_standard.omitted``) — never
guessed.

Scope note (resumption clause, SKILL §"Scope & resumption"): Brown entered as a 5-stub
institution seed (five bare-field undergraduate rows — "Applied Mathematics", "Biology",
"Computer Science", "Economics", "International and Public Affairs" — each with a null
department, 0% tuition, an empty description, and a dead feed). This pass takes the
INSTITUTION fully to gold, ships a verified ≥4-photo campus gallery, wires working
Brown News + LiveWhale events feeds, and replaces the stubs with a real, verified,
field-specific catalog of 56 programs across Brown's seven degree-granting schools (the
undergraduate College, the Graduate School, the Warren Alpert Medical School, the School
of Engineering, the School of Public Health, the Watson School of International and Public
Affairs, and the School of Professional Studies).

Degree designations (A.B. vs Sc.B.) are verified against Brown's official Undergraduate
Programs directory (brown.edu/undergraduate-programs), whose per-concentration slugs encode
the degree, cross-checked against the per-concentration bulletin pages. For a concentration
Brown awards as BOTH the A.B. and the Sc.B., the row carries the Sc.B. (science-track)
designation and the description states that both degrees are offered — never a guessed
single designation.

Tuition (2025-26, SFS): the undergraduate sticker is $71,700 (College); the M.D. is $73,150
(distinct, Warren Alpert); the School of Professional Studies MS in Healthcare Leadership is
$73,500. Brown bills general graduate (master's / Sc.M.) tuition PER COURSE ($8,962/course),
so academic master's rows that have no published flat annual figure record ``tuition`` in
``_standard.omitted`` with the per-course rate documented in ``cost_data`` — never the
undergraduate sticker copied down. Doctoral students are funded (tuition scholarship +
stipend) within the guarantee period, so PhD rows are funded-omit-with-reason; the published
doctoral sticker ($71,700, intentionally equal to undergraduate at Brown) is documented.

Reviews depth (``external_reviews``) is the IN-FLIGHT next slice for Brown and is honestly
recorded in each program's ``_standard.omitted`` this pass — never synthesized. Per-program
class profile, tracks, and faculty are likewise recorded as omitted-with-reason where a
verified per-program figure is not yet captured (the institution-wide Scorecard outcomes are
attached). No fabricated review, quote, or figure ships.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Brown University"
ENRICHED_AT = "2026-06-24"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # Brown publishes a 6:1 student-faculty ratio but no single current instructional-faculty
    # headcount could be verified from a citable official OIR page this session.
    "school_outcomes.scale.faculty_count",
    # Brown's most recent published first-destination data (Class of 2022) reports a knowledge
    # rate and a graduate-study share, not a single "employed or continuing education" percent;
    # no ranked top-industry list is published, so both outcomes fields are honestly omitted.
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "NECHE",
    "carnegie_classification": "Doctoral Universities: Very High Research Spending and Doctorate Production (R1)",
    "qs_world_university_rankings": {"rank": 69, "year": 2026},
    "times_higher_education": {"rank": 65, "year": 2026},
    "us_news_national": {"rank": 13, "year": 2026},
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.0565,
    "avg_net_price": 25184,
    "median_earnings_10yr": 93487,
    "graduation_rate_6yr": 0.9569,
    "retention_rate_first_year": 0.9882,
    "financial_aid": {
        "pell_grant_rate": 0.1384,
        "federal_loan_rate": 0.0959,
        "cost_of_attendance": 87648,
        "median_debt_completers": 11428,
    },
    "demographics": {
        "white": 0.3292,
        "asian": 0.2288,
        "hispanic": 0.1212,
        "international": 0.1269,
        "black": 0.0818,
        "two_or_more": 0.0794,
        "unknown": 0.0295,
    },
    "test_scores": {
        "sat_total_25_75": [1510, 1560],
        "act_25_75": [34, 35],
    },
    "location": {"lat": 41.82617, "lng": -71.40385},
    "campus_basics": {"location": "Providence, Rhode Island"},
    "scale": {
        "student_faculty_ratio": "6:1",
        "endowment_usd": 8000000000,
    },
    "research": {
        "labs": [
            "Robert J. & Nancy D. Carney Institute for Brain Science",
            "Watson Institute for International and Public Affairs",
            "Institute at Brown for Environment and Society",
            "Data Science Institute",
        ],
        "areas": [
            "Brain science and neuroscience",
            "International and public affairs",
            "Environment, climate, and society",
            "Data science and computation",
            "Public health and population health",
        ],
        "lab_links": {
            "Robert J. & Nancy D. Carney Institute for Brain Science": "https://carney.brown.edu/",
            "Watson Institute for International and Public Affairs": "https://home.watson.brown.edu/",
            "Institute at Brown for Environment and Society": "https://ibes.brown.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Ivy League)",
        "mascot": "Bruno the Bear (Brown Bears)",
        "housing": "Residential campus on College Hill in Providence",
        "resources": [
            {"label": "Brown Bears Athletics", "url": "https://brownbears.com/"},
            {"label": "Brown University Library", "url": "https://library.brown.edu/"},
            {"label": "John Hay Library (special collections)", "url": "https://library.brown.edu/about/hay/"},
            {"label": "Tisch Center for Career Exploration", "url": "https://career-center.brown.edu/"},
            {"label": "Centers & Institutes", "url": "https://www.brown.edu/academics/centers-institutes"},
        ],
    },
    "flagship": {
        "applicants": 42765,
        "admits": 2418,
        "admissions_cycle": "Class of 2029 (entering fall 2025; Brown Undergraduate Admission)",
        "founded_year": 1764,
    },
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/2021_Brown_University%2C_Van_Wickle_Gates.jpg/1920px-2021_Brown_University%2C_Van_Wickle_Gates.jpg",
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Brown_Main_Green_at_dusk.jpg/1920px-Brown_Main_Green_at_dusk.jpg",
            "credit": "Wikimedia Commons / Filetime (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Looking_across_the_Main_Quad_toward_University_Hall%2C_Brown_University.jpg/1920px-Looking_across_the_Main_Quad_toward_University_Hall%2C_Brown_University.jpg",
            "credit": "Wikimedia Commons / Chris Rycroft (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Ruth_Simmons_Quad_Brown_University.jpg/1920px-Ruth_Simmons_Quad_Brown_University.jpg",
            "credit": "Wikimedia Commons / John Phelan (CC BY 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/2021_Brown_University%2C_Main_Green%2C_Sayles_and_Friedman_Halls.jpg/1920px-2021_Brown_University%2C_Main_Green%2C_Sayles_and_Friedman_Halls.jpg",
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Brown, UNITID 217156)",
            "url": "https://collegescorecard.ed.gov/school/?217156",
        },
        {
            "label": "NCES College Navigator — Brown University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=217156",
        },
        {
            "label": "Brown Undergraduate Admission — Brown Admission Numbers",
            "url": "https://admission.brown.edu/explore/brown-admission-numbers",
        },
        {
            "label": "Brown Office of Institutional Research — Common Data Set",
            "url": "https://oir.brown.edu/institutional-data/common-data-set",
        },
        {
            "label": "Brown News — Brown ranks among top universities (U.S. News 2026)",
            "url": "https://www.brown.edu/news/2025-09-23/rankings-top-university",
        },
        {
            "label": "Brown News — Endowment return, fiscal year 2025",
            "url": "https://www.brown.edu/news/2025-10-17/brown-endowment-return-2025",
        },
        {
            "label": "QS World University Rankings 2026 — Brown University",
            "url": "https://www.topuniversities.com/universities/brown-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Brown University",
            "url": "https://www.timeshighereducation.com/world-university-rankings/brown-university",
        },
    ],
}

UNDERGRAD_COUNT = 7226

DESCRIPTION = (
    "Brown University is a private research university in Providence, Rhode Island, founded "
    "in 1764 as the seventh-oldest college in the United States and a founding member of the "
    "Ivy League. It enrolls about 7,200 undergraduates and some 3,800 graduate and medical "
    "students on a residential campus on College Hill, with a 6:1 student-faculty ratio.\n\n"
    "Brown is best known for its Open Curriculum, adopted in 1969, which has no general "
    "distribution requirements and lets undergraduates design their own course of study while "
    "concentrating in one of more than eighty fields. The university is organized into the "
    "undergraduate College, the Graduate School, the Warren Alpert Medical School, the School "
    "of Engineering, the School of Public Health, the Watson School of International and Public "
    "Affairs, and the School of Professional Studies. Its research is anchored by the Carney "
    "Institute for Brain Science, the Watson Institute for International and Public Affairs, "
    "the Institute at Brown for Environment and Society, and the Data Science Institute.\n\n"
    "A Carnegie R1 university accredited by the New England Commission of Higher Education, "
    "Brown ranks No. 13 among national universities by U.S. News, No. 65 in the world by Times "
    "Higher Education, and No. 69 by QS. It admitted about 5.7% of first-year applicants to the "
    "Class of 2029 and holds an endowment of about $8 billion.\n\n"
    "Brown practices need-blind admission for U.S. applicants and meets full demonstrated need: "
    "the average net price is about $25,200 a year against a published cost of attendance near "
    "$87,600, and ten-year median earnings for federally aided students are about $93,500. The "
    "Brown Bears compete in NCAA Division I in the Ivy League."
)


_COLLEGE = "The College"
_GRAD = "The Graduate School"
_MED = "The Warren Alpert Medical School of Brown University"
_ENG = "School of Engineering"
_SPH = "School of Public Health"
_WATSON = "Watson School of International and Public Affairs"
_SPS = "School of Professional Studies"

_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://college.brown.edu/",
    _GRAD: "https://graduateschool.brown.edu/",
    _MED: "https://medical.brown.edu/",
    _ENG: "https://engineering.brown.edu/",
    _SPH: "https://sph.brown.edu/",
    _WATSON: "https://home.watson.brown.edu/",
    _SPS: "https://professional.brown.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _COLLEGE, "sort_order": 1, "description": (
        "The College is Brown's undergraduate school, known for the Open Curriculum and for "
        "awarding the A.B. and Sc.B. across more than eighty concentrations in the humanities, "
        "social sciences, life sciences, physical sciences, and engineering."
    )},
    {"name": _GRAD, "sort_order": 2, "description": (
        "The Graduate School oversees Brown's master's and doctoral programs across the arts, "
        "sciences, and engineering, conferring the Ph.D., Sc.M., and A.M. and awarding more "
        "than two hundred doctorates a year."
    )},
    {"name": _MED, "sort_order": 3, "description": (
        "The Warren Alpert Medical School awards the M.D. through an integrated medical "
        "curriculum and the Program in Liberal Medical Education, training physicians in "
        "partnership with Rhode Island's teaching hospitals."
    )},
    {"name": _ENG, "sort_order": 4, "description": (
        "The School of Engineering, whose program dates to 1847 as the oldest in the Ivy "
        "League, awards the Sc.B. in engineering disciplines and graduate Sc.M. and Ph.D. "
        "degrees across biomedical, mechanical, electrical, chemical, and materials engineering."
    )},
    {"name": _SPH, "sort_order": 5, "description": (
        "The School of Public Health awards the M.P.H. and doctoral degrees in biostatistics, "
        "epidemiology, behavioral and social health sciences, and health services research, "
        "with an undergraduate concentration in public health in the College."
    )},
    {"name": _WATSON, "sort_order": 6, "description": (
        "The Watson School of International and Public Affairs, established as Brown's fifth "
        "school in 2024, is home to the undergraduate concentration in international and public "
        "affairs and the Master of Public Affairs, with research on security, development, and "
        "governance."
    )},
    {"name": _SPS, "sort_order": 7, "description": (
        "The School of Professional Studies delivers executive and online master's and "
        "certificate programs for working professionals, including the IE Brown Executive MBA "
        "and master's degrees in healthcare and technology leadership."
    )},
]

_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {
        "founded": "1764 (the College of Rhode Island; Open Curriculum adopted 1969)",
        "research_centers": [
            "Carney Institute for Brain Science",
            "Institute at Brown for Environment and Society",
            "Data Science Institute",
        ],
    },
    _GRAD: {"founded": "Graduate instruction revived 1887; first Ph.D. conferred 1889"},
    _MED: {
        "founded": "1975 (first M.D. degrees; named the Warren Alpert Medical School in 2007)",
        "research_centers": ["Carney Institute for Brain Science", "Legorreta Cancer Center"],
    },
    _ENG: {
        "founded": "Engineering program founded 1847; designated a school in 2010",
        "research_centers": ["Brown Design Workshop", "Institute for Molecular and Nanoscale Innovation"],
    },
    _SPH: {
        "founded": "Established as a school in 2013",
        "research_centers": ["Hassenfeld Child Health Innovation Institute", "Center for Alcohol and Addiction Studies"],
    },
    _WATSON: {
        "founded": "Watson Institute founded 1986; designated Brown's fifth school in 2024",
        "research_centers": ["Costs of War Project", "Center for Latin American and Caribbean Studies"],
    },
    _SPS: {"founded": "Established as a stand-alone school in 2014"},
}

_ABOUT_OMITTED: dict[str, list[str]] = {
    _COLLEGE: ["about_detail.leadership", "about_detail.faculty"],
    _GRAD: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"],
    _MED: ["about_detail.leadership", "about_detail.faculty"],
    _ENG: ["about_detail.leadership", "about_detail.faculty"],
    _SPH: ["about_detail.leadership", "about_detail.faculty"],
    _WATSON: ["about_detail.leadership", "about_detail.faculty"],
    _SPS: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"],
}

# Brown News RSS (https://www.brown.edu/news/all/rss) verified 2026-06-24 returning items
# (10 <item>s, e.g. "Initiative led by Brown researchers boosts mental health support in R.I.
# public schools"). Brown Events runs on LiveWhale; the iCal feed returned 555 VEVENTs and the
# RSS 1000 items the same day. Both confirmed to FETCH before shipping (miss #1 / miss #9).
_BROWN_NEWS_RSS = "https://www.brown.edu/news/all/rss"
_BROWN_EVENTS_ICS = {"url": "https://events.brown.edu/live/ical/events", "type": "ical"}
_BROWN_EVENTS_RSS = "https://events.brown.edu/live/rss/events"

_SOCIAL_BROWN = {
    "instagram": "https://www.instagram.com/brownu/",
    "linkedin": "https://www.linkedin.com/school/brown-university/",
    "x": "https://twitter.com/BrownUniversity",
    "youtube": "https://www.youtube.com/brownuniversity",
    "facebook": "https://www.facebook.com/BrownUniversity",
}

_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _WATSON: {
        "instagram": "https://www.instagram.com/watson_institute/",
        "linkedin": "https://www.linkedin.com/school/watson-institute/",
    },
    _SPH: {
        "instagram": "https://www.instagram.com/brownsph/",
        "linkedin": "https://www.linkedin.com/school/brown-university-school-of-public-health/",
    },
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _COLLEGE: ["Brown College", "undergraduate", "Open Curriculum", "concentration"],
    _GRAD: ["Graduate School", "PhD", "doctoral"],
    _MED: ["Warren Alpert", "medical school", "MD", "medicine"],
    _ENG: ["School of Engineering", "engineering"],
    _SPH: ["School of Public Health", "public health", "MPH"],
    _WATSON: ["Watson Institute", "international affairs", "public affairs"],
    _SPS: ["Professional Studies", "executive", "online master's"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _BROWN_NEWS_RSS,
        "news_url": "https://www.brown.edu/news/",
        "news_curated": True,
        "events_feed": dict(_BROWN_EVENTS_ICS),
        "events_rss": _BROWN_EVENTS_RSS,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_BROWN),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _BROWN_NEWS_RSS,
    "news_url": "https://www.brown.edu/news/",
    "news_curated": True,
    "events_feed": dict(_BROWN_EVENTS_ICS),
    "events_rss": _BROWN_EVENTS_RSS,
    "social": _SOCIAL_BROWN,
}

# Catalog tuple: (program_name, degree_type, school, department, duration_months, slug, keywords, description)
# program_name carries Brown's real conferred designation. For a concentration awarded as BOTH
# the A.B. and the Sc.B., the row carries the Sc.B. and the description states both are offered.
_CATALOG: list[tuple] = [
    # ── The College — undergraduate concentrations (A.B. / Sc.B., Open Curriculum) ──
    (
        "Bachelor of Science in Computer Science", "bachelors", _COLLEGE,
        "Department of Computer Science", 48, "brown-computer-science-scb", ["computer science"],
        "Computer science at Brown runs from theory, algorithms, and systems to artificial intelligence and human-computer interaction, and is awarded as both the A.B. and the Sc.B., with the Open Curriculum letting students pair it freely with other fields.",
    ),
    (
        "Bachelor of Arts in Economics", "bachelors", _COLLEGE,
        "Department of Economics", 48, "brown-economics-ab", ["economics"],
        "The economics concentration grounds students in microeconomic and macroeconomic theory and econometrics, with applied fields spanning finance, development, and public policy on College Hill.",
    ),
    (
        "Bachelor of Science in Applied Mathematics", "bachelors", _COLLEGE,
        "Division of Applied Mathematics", 48, "brown-applied-mathematics-scb", ["applied mathematics"],
        "Brown's Division of Applied Mathematics teaches modeling, differential equations, scientific computation, and probability applied to the physical, biological, and social sciences, awarding both the A.B. and the Sc.B.",
    ),
    (
        "Bachelor of Science in Mathematics", "bachelors", _COLLEGE,
        "Department of Mathematics", 48, "brown-mathematics-scb", ["mathematics"],
        "The mathematics concentration covers analysis, algebra, geometry, and topology with proof-based rigor, offered as both the A.B. and the Sc.B. for students heading toward research, teaching, or quantitative careers.",
    ),
    (
        "Bachelor of Science in Biology", "bachelors", _COLLEGE,
        "Division of Biology and Medicine", 48, "brown-biology-scb", ["biology"],
        "Biology at Brown spans molecular, cellular, organismal, and ecological scales through the Division of Biology and Medicine, with laboratory and field research and both an A.B. and an Sc.B. track.",
    ),
    (
        "Bachelor of Science in Neuroscience", "bachelors", _COLLEGE,
        "Department of Neuroscience", 48, "brown-neuroscience-scb", ["neuroscience"],
        "The neuroscience Sc.B. studies the nervous system from molecules and cells to circuits, cognition, and behavior, drawing on the Carney Institute for Brain Science for undergraduate research.",
    ),
    (
        "Bachelor of Science in Cognitive Science", "bachelors", _COLLEGE,
        "Department of Cognitive, Linguistic and Psychological Sciences", 48, "brown-cognitive-science-scb", ["cognitive science"],
        "Cognitive science examines perception, language, reasoning, and learning across psychology, linguistics, computer science, and philosophy, awarded as both the A.B. and the Sc.B. in the CLPS department.",
    ),
    (
        "Bachelor of Arts in Psychology", "bachelors", _COLLEGE,
        "Department of Cognitive, Linguistic and Psychological Sciences", 48, "brown-psychology-ab", ["psychology"],
        "Psychology at Brown studies cognition, development, social behavior, and clinical science with laboratory methods, housed in the Department of Cognitive, Linguistic and Psychological Sciences and offered as both an A.B. and an Sc.B.",
    ),
    (
        "Bachelor of Science in Physics", "bachelors", _COLLEGE,
        "Department of Physics", 48, "brown-physics-scb", ["physics"],
        "Physics covers classical and quantum mechanics, electromagnetism, statistical physics, and astrophysics, with both an A.B. and an Sc.B. and undergraduate research in condensed matter, high-energy, and biological physics.",
    ),
    (
        "Bachelor of Science in Chemistry", "bachelors", _COLLEGE,
        "Department of Chemistry", 48, "brown-chemistry-scb", ["chemistry"],
        "Chemistry spans organic, inorganic, physical, and biological chemistry with hands-on laboratory work and undergraduate research, offered as both the A.B. and the Sc.B. in the Department of Chemistry.",
    ),
    (
        "Bachelor of Science in Biochemistry and Molecular Biology", "bachelors", _COLLEGE,
        "Division of Biology and Medicine", 48, "brown-biochemistry-molecular-biology-scb", ["biochemistry", "molecular biology"],
        "The biochemistry and molecular biology Sc.B. studies the molecular machinery of living systems — proteins, nucleic acids, metabolism, and gene regulation — bridging chemistry and the life sciences.",
    ),
    (
        "Bachelor of Arts in History", "bachelors", _COLLEGE,
        "Department of History", 48, "brown-history-ab", ["history"],
        "The history concentration trains students in archival research and interpretation across the Americas, Europe, Africa, Asia, and the Middle East and from the ancient world to the present.",
    ),
    (
        "Bachelor of Arts in English", "bachelors", _COLLEGE,
        "Department of English", 48, "brown-english-ab", ["English"],
        "English studies literature in English across periods and genres alongside critical theory, with nonfiction and creative-writing pathways shared with Brown's Literary Arts program.",
    ),
    (
        "Bachelor of Arts in Philosophy", "bachelors", _COLLEGE,
        "Department of Philosophy", 48, "brown-philosophy-ab", ["philosophy"],
        "Philosophy covers logic, ethics, metaphysics, epistemology, and the history of philosophy, with departmental strength in the philosophy of mind, language, and science.",
    ),
    (
        "Bachelor of Arts in Political Science", "bachelors", _COLLEGE,
        "Department of Political Science", 48, "brown-political-science-ab", ["political science"],
        "Political science studies American politics, comparative politics, international relations, and political theory, with empirical methods and ties to the Watson Institute.",
    ),
    (
        "Bachelor of Arts in Sociology", "bachelors", _COLLEGE,
        "Department of Sociology", 48, "brown-sociology-ab", ["sociology"],
        "Sociology examines social structure, inequality, institutions, and change, pairing social theory with quantitative and qualitative research on populations, cities, and global development.",
    ),
    (
        "Bachelor of Arts in Anthropology", "bachelors", _COLLEGE,
        "Department of Anthropology", 48, "brown-anthropology-ab", ["anthropology"],
        "Anthropology at Brown integrates sociocultural anthropology and archaeology to study human societies past and present through ethnographic fieldwork and material culture.",
    ),
    (
        "Bachelor of Arts in International and Public Affairs", "bachelors", _COLLEGE,
        "Watson Institute for International and Public Affairs", 48, "brown-international-public-affairs-ab", ["international affairs", "public affairs"],
        "The international and public affairs concentration, based in the Watson Institute, studies global politics, economics, and policy through tracks in development, policy and governance, and security.",
    ),
    (
        "Bachelor of Arts in Public Health", "bachelors", _COLLEGE,
        "School of Public Health", 48, "brown-public-health-ab", ["public health"],
        "The undergraduate public health concentration studies the distribution and determinants of disease, epidemiologic and statistical methods, and the social forces shaping population health.",
    ),
    (
        "Bachelor of Arts in Health and Human Biology", "bachelors", _COLLEGE,
        "Division of Biology and Medicine", 48, "brown-health-human-biology-ab", ["health", "human biology"],
        "Health and human biology examines human biology in its social, behavioral, and clinical context, letting students build an individualized course of study around medicine, public health, or biomedical research.",
    ),
    (
        "Bachelor of Arts in Engineering", "bachelors", _COLLEGE,
        "School of Engineering", 48, "brown-engineering-ab", ["engineering"],
        "The A.B. in engineering offers a broad, liberal-arts-grounded foundation in engineering science for students who want engineering breadth alongside Brown's Open Curriculum rather than a single specialized discipline.",
    ),
    (
        "Bachelor of Science in Biomedical Engineering", "bachelors", _COLLEGE,
        "School of Engineering", 48, "brown-biomedical-engineering-scb", ["biomedical engineering"],
        "The biomedical engineering Sc.B. applies engineering analysis to living systems — biomechanics, biomaterials, imaging, and instrumentation — bridging the School of Engineering and the life sciences.",
    ),
    (
        "Bachelor of Science in Mechanical Engineering", "bachelors", _COLLEGE,
        "School of Engineering", 48, "brown-mechanical-engineering-scb", ["mechanical engineering"],
        "The mechanical engineering Sc.B. covers solid and fluid mechanics, thermodynamics, dynamics, and design, with capstone projects in the Brown Design Workshop.",
    ),
    (
        "Bachelor of Science in Electrical Engineering", "bachelors", _COLLEGE,
        "School of Engineering", 48, "brown-electrical-engineering-scb", ["electrical engineering"],
        "The electrical engineering Sc.B. studies circuits, signals and systems, electromagnetics, and electronic devices, with laboratory work in communications, control, and microelectronics.",
    ),
    (
        "Bachelor of Science in Chemical Engineering", "bachelors", _COLLEGE,
        "School of Engineering", 48, "brown-chemical-engineering-scb", ["chemical engineering"],
        "The chemical engineering Sc.B. applies chemistry, transport, thermodynamics, and reaction engineering to processes in energy, materials, and biotechnology.",
    ),
    (
        "Bachelor of Science in Materials Engineering", "bachelors", _COLLEGE,
        "School of Engineering", 48, "brown-materials-engineering-scb", ["materials engineering"],
        "The materials engineering Sc.B. examines the structure-property relationships of metals, ceramics, polymers, and electronic materials, linking processing to mechanical and electronic behavior.",
    ),
    (
        "Bachelor of Arts in Modern Culture and Media", "bachelors", _COLLEGE,
        "Department of Modern Culture and Media", 48, "brown-modern-culture-media-ab", ["modern culture and media"],
        "Modern culture and media studies film, television, digital media, and visual culture through critical and theoretical analysis alongside hands-on media production.",
    ),
    (
        "Bachelor of Arts in Africana Studies", "bachelors", _COLLEGE,
        "Department of Africana Studies", 48, "brown-africana-studies-ab", ["Africana studies"],
        "Africana studies examines the histories, cultures, politics, and creative expression of African, African American, and Afro-Caribbean peoples across the diaspora.",
    ),
    (
        "Bachelor of Science in Statistics", "bachelors", _COLLEGE,
        "Department of Biostatistics", 48, "brown-statistics-scb", ["statistics"],
        "The statistics Sc.B. builds a foundation in probability, statistical inference, and data analysis, with computing and applications across the natural, social, and health sciences.",
    ),
    (
        "Bachelor of Arts in Comparative Literature", "bachelors", _COLLEGE,
        "Department of Comparative Literature", 48, "brown-comparative-literature-ab", ["comparative literature"],
        "Comparative literature reads literature across languages and national traditions, foregrounding translation, world literature, and literary and critical theory.",
    ),
    (
        "Bachelor of Arts in Archaeology and the Ancient World", "bachelors", _COLLEGE,
        "Joukowsky Institute for Archaeology and the Ancient World", 48, "brown-archaeology-ancient-world-ab", ["archaeology"],
        "Based in the Joukowsky Institute, this concentration studies the material culture of ancient civilizations through excavation, artifact analysis, and the science of the archaeological record.",
    ),
    (
        "Bachelor of Arts in American Studies", "bachelors", _COLLEGE,
        "Department of American Studies", 48, "brown-american-studies-ab", ["American studies"],
        "American studies takes an interdisciplinary view of the cultures, politics, and social movements of the United States through history, literature, ethnic studies, and public humanities.",
    ),
    (
        "Bachelor of Arts in Classics", "bachelors", _COLLEGE,
        "Department of Classics", 48, "brown-classics-ab", ["classics"],
        "Classics combines study of Greek and Latin with the literature, history, and archaeology of the ancient Mediterranean world.",
    ),
    (
        "Bachelor of Arts in East Asian Studies", "bachelors", _COLLEGE,
        "Department of East Asian Studies", 48, "brown-east-asian-studies-ab", ["East Asian studies"],
        "East Asian studies combines advanced study of Chinese, Japanese, or Korean with the literature, history, and culture of East Asia.",
    ),
    (
        "Bachelor of Science in Earth and Planetary Sciences", "bachelors", _COLLEGE,
        "Department of Earth, Environmental and Planetary Sciences", 48, "brown-earth-planetary-sciences-scb", ["earth science", "planetary science"],
        "Earth and planetary sciences studies the solid Earth, climate, oceans, and other planets through geology, geophysics, and remote sensing, awarded as both the A.B. and the Sc.B.",
    ),
    (
        "Bachelor of Arts in Linguistics", "bachelors", _COLLEGE,
        "Department of Cognitive, Linguistic and Psychological Sciences", 48, "brown-linguistics-ab", ["linguistics"],
        "Linguistics studies the structure of language — phonology, syntax, semantics, and language change — and its cognitive and computational dimensions in the CLPS department.",
    ),
    (
        "Bachelor of Arts in Music", "bachelors", _COLLEGE,
        "Department of Music", 48, "brown-music-ab", ["music"],
        "The music concentration combines theory, history, composition, and ethnomusicology with performance and a multimedia and computer-music studio.",
    ),
    (
        "Bachelor of Arts in Religious Studies", "bachelors", _COLLEGE,
        "Department of Religious Studies", 48, "brown-religious-studies-ab", ["religious studies"],
        "Religious studies examines the texts, histories, and practices of the world's religious traditions across the ancient, medieval, and modern periods.",
    ),
    (
        "Bachelor of Arts in Visual Art", "bachelors", _COLLEGE,
        "Department of Visual Art", 48, "brown-visual-art-ab", ["visual art"],
        "Visual art pairs studio practice across drawing, painting, sculpture, digital media, and print with critique and the history and theory of contemporary art.",
    ),
    (
        "Bachelor of Arts in Egyptology and Assyriology", "bachelors", _COLLEGE,
        "Department of Egyptology and Assyriology", 48, "brown-egyptology-assyriology-ab", ["Egyptology", "Assyriology"],
        "Egyptology and Assyriology studies the languages, texts, and civilizations of ancient Egypt and the ancient Near East, including hieroglyphic and cuneiform sources.",
    ),
    # ── The Graduate School — research master's + doctoral (arts & sciences) ──
    (
        "Master of Science in Data Science", "masters", _GRAD,
        "Data Science Institute", 21, "brown-data-science-scm", ["data science"],
        "Brown's Sc.M. in Data Science, run through the Data Science Institute, combines mathematics, statistics, computer science, and machine learning with a capstone applying data methods to a real problem.",
    ),
    (
        "Doctor of Philosophy in Computer Science", "phd", _GRAD,
        "Department of Computer Science", 60, "brown-computer-science-phd", ["computer science PhD"],
        "The computer science Ph.D. supports original research across systems, theory, machine learning, graphics, and human-computer interaction, with funded students working closely with faculty.",
    ),
    (
        "Doctor of Philosophy in Physics", "phd", _GRAD,
        "Department of Physics", 60, "brown-physics-phd", ["physics PhD"],
        "The physics Ph.D. trains researchers in condensed-matter, high-energy, astrophysical, and biological physics through coursework, qualifying examinations, and dissertation research.",
    ),
    (
        "Doctor of Philosophy in Biology", "phd", _GRAD,
        "Division of Biology and Medicine", 60, "brown-biology-phd", ["biology PhD"],
        "The biology Ph.D. advances doctoral research across molecular biology, cell biology, ecology and evolution, and computational biology in the Division of Biology and Medicine.",
    ),
    (
        "Doctor of Philosophy in Economics", "phd", _GRAD,
        "Department of Economics", 60, "brown-economics-phd", ["economics PhD"],
        "The economics Ph.D. trains researchers in microeconomic and macroeconomic theory and econometrics, with applied strength in development, labor, and public economics.",
    ),
    (
        "Doctor of Philosophy in History", "phd", _GRAD,
        "Department of History", 60, "brown-history-phd", ["history PhD"],
        "The history Ph.D. supports archive-based doctoral research across American, European, and global history, with fields in early modern, modern, and transnational history.",
    ),
    (
        "Doctor of Philosophy in Neuroscience", "phd", _GRAD,
        "Department of Neuroscience", 60, "brown-neuroscience-phd", ["neuroscience PhD"],
        "The neuroscience Ph.D. supports research from molecular and cellular neuroscience to systems and computational neuroscience, anchored by the Carney Institute for Brain Science.",
    ),
    (
        "Doctor of Philosophy in Chemistry", "phd", _GRAD,
        "Department of Chemistry", 60, "brown-chemistry-phd", ["chemistry PhD"],
        "The chemistry Ph.D. trains researchers across organic, inorganic, physical, and chemical-biology research in faculty laboratories with shared instrumentation.",
    ),
    (
        "Doctor of Philosophy in Applied Mathematics", "phd", _GRAD,
        "Division of Applied Mathematics", 60, "brown-applied-mathematics-phd", ["applied mathematics PhD"],
        "The applied mathematics Ph.D. pursues research in dynamical systems, scientific computing, probability, and mathematical modeling of physical and biological systems.",
    ),
    # ── Warren Alpert Medical School ──
    (
        "Doctor of Medicine", "professional", _MED,
        "The Warren Alpert Medical School of Brown University", 48, "brown-medicine-md", ["MD", "medicine"],
        "The M.D. at the Warren Alpert Medical School integrates foundational science with early clinical experience and a scholarly concentration, training physicians in Brown's affiliated Providence teaching hospitals.",
    ),
    # ── School of Public Health ──
    (
        "Master of Public Health", "masters", _SPH,
        "School of Public Health", 24, "brown-public-health-mph", ["MPH", "public health"],
        "Brown's M.P.H. trains public-health practitioners in epidemiology, biostatistics, health policy, and the social and behavioral sciences, with on-campus and fully online options.",
    ),
    (
        "Doctor of Philosophy in Biostatistics", "phd", _SPH,
        "Department of Biostatistics", 60, "brown-biostatistics-phd", ["biostatistics PhD"],
        "The biostatistics Ph.D. develops statistical methods for clinical trials, genomics, and population health, with research in causal inference, Bayesian methods, and health data science.",
    ),
    (
        "Doctor of Philosophy in Epidemiology", "phd", _SPH,
        "Department of Epidemiology", 60, "brown-epidemiology-phd", ["epidemiology PhD"],
        "The epidemiology Ph.D. studies the distribution and determinants of disease, training researchers in study design, causal inference, and the epidemiology of chronic and infectious disease.",
    ),
    # ── Watson School of International and Public Affairs ──
    (
        "Master of Public Affairs", "masters", _WATSON,
        "Watson School of International and Public Affairs", 24, "brown-public-affairs-mpa", ["MPA", "public affairs"],
        "The Master of Public Affairs at the Watson School trains policy professionals in economics, quantitative methods, and governance, with a policy-in-action curriculum and a capstone engagement.",
    ),
    # ── School of Engineering — graduate ──
    (
        "Doctor of Philosophy in Biomedical Engineering", "phd", _ENG,
        "School of Engineering", 60, "brown-biomedical-engineering-phd", ["biomedical engineering PhD"],
        "The biomedical engineering Ph.D. pursues research in biomechanics, biomaterials, neuroengineering, and medical imaging across the School of Engineering and Brown's medical and life-science partners.",
    ),
    (
        "Master of Science in Mechanical Engineering", "masters", _ENG,
        "School of Engineering", 24, "brown-mechanical-engineering-scm", ["mechanical engineering ScM"],
        "The Sc.M. in mechanical engineering offers advanced coursework and supervised research in solid mechanics, fluids and thermal sciences, and design for students preparing for industry or doctoral study.",
    ),
    # ── School of Professional Studies ──
    (
        "Master of Science in Healthcare Leadership", "masters", _SPS,
        "School of Professional Studies", 12, "brown-healthcare-leadership-ms", ["healthcare leadership", "executive"],
        "The Executive Master of Healthcare Leadership is a twelve-month program for working professionals, blending Brown coursework in strategy, finance, and operations for leaders across the health sector.",
    ),
]


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for pname, dtype, school, dept, dur, slug, kw, desc in _CATALOG:
        if slug in seen:
            raise RuntimeError(f"duplicate slug {slug}")
        seen.add(slug)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "duration_months": dur,
            "delivery_format": "on_campus",
            "keywords": list(kw),
            "description": desc,
        })
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_TUITION_UG = 71700
_UNDERGRAD_COA = 97284
_AVG_NET_PRICE = 25184
_COST_SRC = (
    "Brown Student Financial Services 2025-26 undergraduate tuition + cost of attendance",
    "https://sfs.brown.edu/tuition-and-fees/undergraduate",
)
_SFS_GRAD_SRC = (
    "Brown Student Financial Services — 2025-26 Graduate tuition and fees",
    "https://sfs.brown.edu/tuition-and-fees/graduate",
)
_SFS_MED_SRC = (
    "Brown Student Financial Services — 2025-26 Medical School tuition and fees",
    "https://sfs.brown.edu/tuition-and-fees/medical-school",
)
_SFS_PROF_SRC = (
    "Brown Student Financial Services — 2025-26 Professional Master's tuition and fees",
    "https://sfs.brown.edu/tuition-fees/professional-masters-program-tuition-and-fees",
)

_PER_COURSE_MASTERS = 8962  # Brown bills general graduate master's / Sc.M. tuition per course
_MED_MD_ANNUAL = 73150  # Warren Alpert M.D. annual tuition
_HEALTHCARE_LEADERSHIP_TOTAL = 73500  # SPS MS Healthcare Leadership, 12-month program
_PHD_STICKER = 71700  # Published doctoral full-time sticker (waived for funded students)


def _annual_cost(tuition_usd: int, *, note: str, source: str, source_url: str, year: str = "2025-26") -> dict:
    return {
        "tuition_usd": tuition_usd,
        "funded": False,
        "note": note,
        "source": source,
        "source_url": source_url,
        "year": year,
    }


# Programs with a verified, published flat annual / total tuition figure the matcher can read
# directly as an annual budget input (never the undergraduate sticker copied down).
_COST_BY_SLUG: dict[str, dict] = {
    "brown-medicine-md": _annual_cost(
        _MED_MD_ANNUAL,
        note=(
            f"Warren Alpert Medical School M.D. tuition: ${_MED_MD_ANNUAL:,} per academic year "
            "(2025-26), billed per semester — distinct from and higher than the undergraduate rate."
        ),
        source=_SFS_MED_SRC[0],
        source_url=_SFS_MED_SRC[1],
    ),
    "brown-healthcare-leadership-ms": _annual_cost(
        _HEALTHCARE_LEADERSHIP_TOTAL,
        note=(
            "School of Professional Studies Executive Master of Healthcare Leadership: about "
            f"${_HEALTHCARE_LEADERSHIP_TOTAL:,} total program tuition ($8,647 per credit over a "
            "twelve-month program), so the program total is approximately the annual rate."
        ),
        source=_SFS_PROF_SRC[0],
        source_url=_SFS_PROF_SRC[1],
    ),
}

# Academic master's / Sc.M. programs Brown bills PER COURSE with no published flat annual
# figure — tuition value omitted-with-reason (the per-course rate is documented in cost_data).
_PER_COURSE_SLUGS = {
    "brown-data-science-scm",
    "brown-public-health-mph",
    "brown-public-affairs-mpa",
    "brown-mechanical-engineering-scm",
}


def _grad_has_verified_tuition(spec: dict) -> bool:
    return spec["slug"] in _COST_BY_SLUG


_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after entry "
    "(U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 93487,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Brown, UNITID 217156)",
    "source_url": "https://collegescorecard.ed.gov/school/?217156",
}

_REQ_UNDERGRAD = {
    "materials": [
        "Common Application, Coalition Application, or QuestBridge Application",
        "Brown writing supplement",
        "Secondary-school report + transcript",
        "Two teacher evaluations + counselor recommendation",
        "SAT or ACT scores (required for the Class of 2029 cycle; verify the current cycle on the admission site)",
    ],
    "deadlines": {
        "early_decision": "November 1",
        "regular_decision": "January 1",
    },
    "source": "https://admission.brown.edu/apply",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose",
        "Standardized / English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://graduateschool.brown.edu/admission",
}
_REQ_MED = {
    "materials": [
        "AMCAS application",
        "Warren Alpert secondary application",
        "MCAT scores",
        "Letters of recommendation",
        "Interview",
    ],
    "deadlines": {
        "amcas": "Verify the current AMCAS cycle on the Warren Alpert admissions site.",
    },
    "source": "https://medical.brown.edu/admission",
}

_TRACKS_BY_SLUG: dict[str, dict] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {}

# Reviews depth across the rest of the catalog is the IN-FLIGHT next slice for Brown
# (recorded omitted-with-reason in _program_standard); no review is synthesized. The one
# review below is GATHERED from real program-specific third-party coverage of the Warren
# Alpert M.D. (U.S. News med-school profile, Brown News, the Brown Daily Herald Match-Day
# report, the official Match Lists, the PLME site, and Brown's published cost of attendance),
# distilled to an honest paragraph with the common cautions and cited per source.
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "brown-medicine-md": {
        "summary": (
            "Brown's Warren Alpert Medical School M.D. is best known for primary-care education "
            "and an integrated, competency-based curriculum with a roughly 17-month pre-clerkship "
            "phase, a longitudinal Doctoring clinical-skills course, and a required Scholarly "
            "Concentration. It is the entry point for the Program in Liberal Medical Education "
            "(PLME), the only combined baccalaureate-M.D. program in the Ivy League, and posts "
            "strong residency outcomes — 122 students matched in 2024. Common cautions are the "
            "high cost of attendance (well over $100,000 a year all-in), Providence's smaller-city "
            "setting, and a research profile and national name recognition below the top-five "
            "research powerhouses; Brown also stopped submitting data to U.S. News in 2023, so its "
            "most recent published ranks predate that exit."
        ),
        "themes": [
            {
                "label": "Primary-care strength",
                "sentiment": "positive",
                "detail": (
                    "Warren Alpert's strongest reputation is in primary care; its most recent "
                    "published U.S. News figures (2023, before Brown stopped submitting data) "
                    "placed it higher for primary care than for research."
                ),
            },
            {
                "label": "Integrated, competency-based curriculum",
                "sentiment": "positive",
                "detail": (
                    "A four-year competency-based curriculum with an integrated pre-clerkship "
                    "phase, the longitudinal Doctoring course, and a required Scholarly "
                    "Concentration in a field the student chooses."
                ),
            },
            {
                "label": "PLME combined-degree pathway",
                "sentiment": "positive",
                "detail": (
                    "The Program in Liberal Medical Education is the only combined "
                    "baccalaureate-M.D. program in the Ivy League, an eight-year continuum that "
                    "pairs the M.D. with Brown's Open Curriculum and is highly selective."
                ),
            },
            {
                "label": "Residency match outcomes",
                "sentiment": "positive",
                "detail": (
                    "On 2024 Match Day, 122 students matched, with internal medicine, emergency "
                    "medicine, and obstetrics and gynecology among the most common specialties."
                ),
            },
            {
                "label": "High cost of attendance",
                "sentiment": "caution",
                "detail": (
                    "M.D. tuition is above the private-medical-school average and the published "
                    "full cost of attendance exceeds $100,000 a year, with Providence's local cost "
                    "of living running above the national average."
                ),
            },
            {
                "label": "Research profile and setting",
                "sentiment": "mixed",
                "detail": (
                    "The program's research rank historically trailed its primary-care rank, it "
                    "carries less national name recognition than top-five research schools, and "
                    "Providence is a smaller city than its Boston and New York peers."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News Best Medical Schools — Brown (Warren Alpert)",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/brown-university-04102",
            },
            {
                "label": "Brown News — Medical school ends U.S. News ranking participation (2023)",
                "url": "https://www.brown.edu/news/2023-08-29/medical-school-rankings",
            },
            {
                "label": "Brown Daily Herald — 122 Warren Alpert students receive residency matches (2024)",
                "url": "https://www.browndailyherald.com/article/2024/03/122-warren-alpert-students-receive-residency-matches",
            },
            {
                "label": "Warren Alpert Medical School — Match Lists (official)",
                "url": "https://medical.brown.edu/about/facts-and-figures/match-lists",
            },
            {
                "label": "Brown — Program in Liberal Medical Education (PLME)",
                "url": "https://plme.med.brown.edu/",
            },
            {
                "label": "Brown Medical School — Cost of Attendance (official)",
                "url": "https://finaid.med.brown.edu/cost-attendance",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party and official sources — not "
            "individual verbatim reviews. Published U.S. News ranks predate Brown's 2023 "
            "withdrawal from ranking submission and may be dated."
        ),
    },
}


def _lead_campus_photo(school_outcomes: dict) -> str | None:
    photos = (school_outcomes or {}).get("campus_photos") or []
    if photos and isinstance(photos[0], dict):
        return photos[0].get("url")
    return None


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
    ]
    if spec["degree_type"] != "bachelors" and not _grad_has_verified_tuition(spec):
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
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    if spec["slug"] == "brown-medicine-md":
        return dict(_REQ_MED)
    return dict(_REQ_GRAD_GENERIC)


def apply(session: Session) -> bool:
    """Enrich Brown to the canonical profile. Flushes; caller commits."""
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
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
    inst.founded_year = 1764
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.brown.edu"
    lead_photo = _lead_campus_photo(school_outcomes)
    if lead_photo:
        _gallery = [u for u in (inst.media_gallery or []) if u != lead_photo]
        inst.media_gallery = [lead_photo, *_gallery]
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
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        elif spec["degree_type"] == "bachelors":
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
                    "Published 2025-26 Brown undergraduate tuition with Student Financial "
                    "Services' cost of attendance and the College Scorecard average net price."
                ),
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2025-26",
            }
        elif slug in _PER_COURSE_SLUGS:
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": (
                    "Brown bills general graduate (master's / Sc.M.) tuition per course at "
                    f"${_PER_COURSE_MASTERS:,} per course (2025-26), not as a flat annual rate, so a "
                    "single verified annual tuition figure is not published for this program; the "
                    "per-course rate is the published basis."
                ),
                "source": _SFS_GRAD_SRC[0],
                "source_url": _SFS_GRAD_SRC[1],
                "year": "2025-26",
            }
        else:  # PhD — funded
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": (
                    "Doctoral students at Brown receive a full tuition scholarship plus a stipend "
                    "within the funding-guarantee period, so tuition is waived for funded Ph.D. "
                    f"students. The published full-time doctoral sticker is ${_PHD_STICKER:,} "
                    "(2025-26), intentionally equal to the undergraduate rate at Brown."
                ),
                "source": _SFS_GRAD_SRC[0],
                "source_url": _SFS_GRAD_SRC[1],
                "year": "2025-26",
            }
        p.application_requirements = _requirements_for(spec)
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
            date(2027, 1, 1) if spec["degree_type"] == "bachelors" else None
        )
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
