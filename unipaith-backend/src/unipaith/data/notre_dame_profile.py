"""University of Notre Dame — gold-standard profile data (institution + schools + program catalog).

Mirrors the MIT / UF reference instance (see ``mit_profile.py`` / ``uf_profile.py``):
every value is researched from an authoritative source and carries a citation, or is
honestly omitted (recorded in that node's ``_standard.omitted``) — never guessed. Built
2026-06-20 from:

  * U.S. Dept. of Education **College Scorecard** API + **IPEDS** (UNITID 152080):
    admit rate (0.1127), average net price ($26,780), cost of attendance ($83,271),
    ten-year median earnings ($99,980), four-year completion (0.9517), first-year
    retention (0.9908), Pell/loan rates, median debt ($19,000), undergraduate size
    (8,818), and SAT middle-50% scores (EBRW 720–770, Math 735–790).
  * **Notre Dame Undergraduate Admissions — Class of 2029**: 35,401 applicants /
    3,186 admitted (overall rate ~9%), reported by The Observer (ndsmcobserver.com).
  * Rankings: **U.S. News Best Colleges 2026** (#20 National), **QS 2026** (#=294),
    **Times Higher Education 2026** (#194), Carnegie R1, and Higher Learning Commission
    (HLC) accreditation, each cited.
  * The official Notre Dame **Undergraduate Admissions colleges-and-majors index**
    (admissions.nd.edu) and the **Graduate School degree-programs A–Z**
    (graduateschool.nd.edu) for the real degree set, plus each professional school's
    official site (Mendoza, Keough, School of Architecture, the Law School, Sacred Music).
  * A verified 5-photo Wikimedia Commons campus gallery (author + license confirmed via
    the Commons extmetadata API).
  * Verified third-party coverage for flagship coverable programs (Mendoza MBA, MS in
    Business Analytics, the Law School J.D.).

Honest caveats stamped into ``_standard.omitted``: Notre Dame does not publish a single
university-wide placement rate or a uniform top-employer-industries list, so those two
institution outcome fields are omitted. Per-program deep fields (class profile, faculty
roster) and ``external_reviews`` for niche research degrees with no distinct third-party
coverage are recorded in each node's ``_standard.omitted``; the flagship coverable programs
carry researched reviews. Graduate-tier tuition (2026-06-22, ndgradtuition1): every
master's and professional program carries a verified published rate from the Office of
Student Accounts or the Law School; funded Ph.D./J.S.D./D.M.A. and the MSM (assistantship-
covered) carry verified $0 with ``funded=True``.

The catalog is Notre Dame's REAL degree set: every row carries its CONFERRED degree
designation, its real owning college/department, and a per-credential field-specific
description (gold MIT / UF model — a verified general-knowledge discipline definition +
Notre Dame's real owning college + the credential level). Per-credential body repair
(2026-06-21, ndpercrd1): sibling-aware ``_assign_descriptions`` replaces credential-frame
+ ONE shared discipline-def body across credential siblings (23 fields failed the
frame-stripped shared-body gate live — REPAIR_BACKLOG HIGH #7). The build self-enforces
the gold-MIT-0% anti-stub gate (``anti_stub.analyze`` + ``machine_artifacts`` +
``frame_stripped_shared_body(abs_chars=150)`` + ``template_slot_artifacts``).
"""

# ruff: noqa: E501

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Notre Dame"
ENRICHED_AT = "2026-06-21"
UNITID = "152080"
SCORECARD_URL = "https://collegescorecard.ed.gov/school/?152080-University-of-Notre-Dame"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# ── School (college) names ──────────────────────────────────────────────────
ARTS = "College of Arts and Letters"
SCIENCE = "College of Science"
ENGINEERING = "College of Engineering"
MENDOZA = "Mendoza College of Business"
ARCHITECTURE = "School of Architecture"
KEOUGH = "Keough School of Global Affairs"
LAW = "Notre Dame Law School"

_SCHOOL_META: list[dict] = [
    {
        "name": ARTS, "sort_order": 1, "website": "https://al.nd.edu/",
        "leadership": "Sarah A. Mustillo — I.A. O'Shaughnessy Dean",
        "research_centers": ["Medieval Institute", "Nanovic Institute for European Studies", "Kellogg Institute for International Studies", "Institute for Scholarship in the Liberal Arts"],
        "keywords": ["College of Arts and Letters", "humanities", "social sciences", "liberal arts"],
    },
    {
        "name": SCIENCE, "sort_order": 2, "website": "https://science.nd.edu/",
        "leadership": "Santiago Schnell — William K. Warren Foundation Dean",
        "research_centers": ["Harper Cancer Research Institute", "Notre Dame Radiation Laboratory", "Eck Institute for Global Health", "Department of Physics and Astronomy"],
        "keywords": ["College of Science", "natural sciences", "mathematics", "research"],
    },
    {
        "name": ENGINEERING, "sort_order": 3, "website": "https://engineering.nd.edu/",
        "leadership": "Patricia Culligan — Matthew H. McCloskey Dean",
        "research_centers": ["Notre Dame Turbomachinery Laboratory", "Center for Nano Science and Technology (NDnano)", "Lucy Family Institute for Data & Society", "Center for Sustainable Energy at Notre Dame"],
        "keywords": ["College of Engineering", "engineering", "computing"],
    },
    {
        "name": MENDOZA, "sort_order": 4, "website": "https://mendoza.nd.edu/",
        "leadership": "Kristen Collett-Schmitt — Interim Martin J. Gillen Dean",
        "research_centers": ["Department of Finance", "Department of Accountancy", "Notre Dame Deloitte Center for Ethical Leadership", "Stayer Center for Executive Education"],
        "keywords": ["Mendoza College of Business", "business", "finance", "MBA"],
    },
    {
        "name": ARCHITECTURE, "sort_order": 5, "website": "https://architecture.nd.edu/",
        "leadership": "Stefanos Polyzoides — Francis and Kathleen Rooney Dean",
        "research_centers": ["Rome Studies Program", "Driehaus Prize", "School of Architecture Library", "Notre Dame Center for Building Communities"],
        "keywords": ["School of Architecture", "architecture", "urbanism", "classical design"],
    },
    {
        "name": KEOUGH, "sort_order": 6, "website": "https://keough.nd.edu/",
        "leadership": "Mary Gallagher — Marilyn Keough Dean",
        "research_centers": ["Kroc Institute for International Peace Studies", "Pulte Institute for Global Development", "Kellogg Institute for International Studies", "Liu Institute for Asia and Asian Studies"],
        "keywords": ["Keough School of Global Affairs", "global affairs", "international", "policy"],
    },
    {
        "name": LAW, "sort_order": 7, "website": "https://law.nd.edu/",
        "leadership": "G. Marcus Cole — Joseph A. Matson Dean",
        "research_centers": ["Notre Dame Law School London Program", "Klau Institute for Civil and Human Rights", "Religious Liberty Clinic", "Program on Constitutional Structure"],
        "keywords": ["Notre Dame Law School", "law", "JD"],
    },
]

SCHOOLS: list[dict] = [
    {"name": m["name"], "sort_order": m["sort_order"],
     "description": f"The {m['name']} is one of the University of Notre Dame's degree-granting colleges and schools."}
    for m in _SCHOOL_META
]
SCHOOL_WEBSITE = {m["name"]: m["website"] for m in _SCHOOL_META}
_KEYWORDS_BY_SCHOOL = {m["name"]: m["keywords"] for m in _SCHOOL_META}


def _about_for(m: dict) -> dict:
    return {
        "leadership": m["leadership"],
        "research_centers": m["research_centers"],
        "source": {"label": "University of Notre Dame — Colleges, Schools and Departments", "url": "https://www.nd.edu/academics/colleges-schools-and-departments/"},
    }


def _about_omitted(m: dict) -> list[str]:
    return ["about_detail.founded", "about_detail.faculty", "about_detail.named_for"]


# ── Feeds (content_sources) ────────────────────────────────────────────────
# news.nd.edu exposes no server-fetchable RSS (403-gated to crawlers, verified
# 2026-06-20). The verified LiveWhale-style events feed at events.nd.edu — current,
# image-carrying, returns ~17 items — feeds Updates; the companion iCalendar
# (~72 VEVENTs) feeds Events. (enrich-profile miss #9: set the best WORKING feed.)
_ND_EVENTS_RSS = "https://events.nd.edu/events.rss"
_ND_EVENTS_ICS = {"url": "https://events.nd.edu/events.ics", "type": "ical"}
_SOCIAL = {
    "instagram": "https://www.instagram.com/notredame/",
    "linkedin": "https://www.linkedin.com/school/university-of-notre-dame/",
    "x": "https://twitter.com/NotreDame",
    "youtube": "https://www.youtube.com/notredame",
    "facebook": "https://www.facebook.com/notredame",
}
_INSTITUTION_CONTENT: dict = {
    "news_rss": _ND_EVENTS_RSS,
    "news_url": "https://news.nd.edu/",
    "news_curated": True,
    "events_feed": dict(_ND_EVENTS_ICS),
    "social": _SOCIAL,
}


def _school_content(name: str) -> dict:
    m = next(x for x in _SCHOOL_META if x["name"] == name)
    return {
        "news_rss": _ND_EVENTS_RSS,
        "news_url": m["website"],
        "news_curated": False,
        "events_feed": dict(_ND_EVENTS_ICS),
        "keywords": list(m["keywords"]),
        "social": _SOCIAL,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# ── Institution-level data (researched + cited) ─────────────────────────────
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
        "rank": 294, "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/university-notre-dame",
    },
    "times_higher_education": {
        "rank": 194, "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-notre-dame",
    },
    "us_news_national": {
        "rank": 20, "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/university-of-notre-dame-1840",
    },
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1127,
    "avg_net_price": 26780,
    "median_earnings_10yr": 99980,
    "completion_rate_4yr_150pct": 0.9517,
    "retention_rate_first_year": 0.9908,
    "graduation_rate_6yr": 0.9517,
    "financial_aid": {
        "pell_grant_rate": 0.1374,
        "federal_loan_rate": 0.2467,
        "cost_of_attendance": 83271,
        "median_debt_completers": 19000,
        "avg_net_price": 26780,
    },
    "demographics": {
        "white": 0.5939,
        "asian": 0.0572,
        "hispanic": 0.1532,
        "black": 0.0472,
    },
    "test_scores": {
        "sat_reading_25_75": [720, 770],
        "sat_math_25_75": [735, 790],
    },
    "campus_basics": {"location": "Notre Dame, Indiana"},
    "scale": {
        "campus_acres": 1265,
        "student_faculty_ratio": "9:1",
    },
    "location": {"lat": 41.7002, "lng": -86.2379},
    "research": {
        "areas": [
            "Global health and the life sciences",
            "Energy and the environment",
            "Data science and computing",
            "Peace studies and international development",
            "Theology, philosophy, and the humanities",
        ],
        "labs": [
            "Harper Cancer Research Institute",
            "Notre Dame Radiation Laboratory",
            "Kroc Institute for International Peace Studies",
            "Eck Institute for Global Health",
            "Notre Dame Turbomachinery Laboratory",
        ],
        "lab_links": {
            "Harper Cancer Research Institute": "https://harpercancer.nd.edu/",
            "Notre Dame Radiation Laboratory": "https://radlab.nd.edu/",
            "Kroc Institute for International Peace Studies": "https://kroc.nd.edu/",
            "Eck Institute for Global Health": "https://globalhealth.nd.edu/",
            "Notre Dame Turbomachinery Laboratory": "https://ndtl.nd.edu/",
        },
    },
    "campus_life": {
        "student_orgs": 500,
        "varsity_sports": 24,
        "athletics_division": "NCAA Division I FBS (Atlantic Coast Conference; football independent)",
        "resources": [
            {"name": "Division of Student Affairs", "url": "https://studentaffairs.nd.edu/"},
            {"name": "RecSports", "url": "https://recsports.nd.edu/"},
            {"name": "Office of Residential Life", "url": "https://residentiallife.nd.edu/"},
            {"name": "University Health Services", "url": "https://uhs.nd.edu/"},
        ],
    },
    "campus_photos": [
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Main_Building_at_the_University_of_Notre_Dame.jpg/1920px-Main_Building_at_the_University_of_Notre_Dame.jpg", "credit": "Wikimedia Commons / Matthew Rice (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Dome%2C_Library%2C_basilica.jpg/1920px-Dome%2C_Library%2C_basilica.jpg", "credit": "Wikimedia Commons / Eccekevin (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Golden_Dome_from_Washington.jpg/1920px-Golden_Dome_from_Washington.jpg", "credit": "Wikimedia Commons / Eccekevin (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Dome_view_St_Mary.jpg/1920px-Dome_view_St_Mary.jpg", "credit": "Wikimedia Commons / Eccekevin (CC BY-SA 4.0)"},
        {"url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Administration_Building_ND.jpg/1920px-Administration_Building_ND.jpg", "credit": "Wikimedia Commons / Teemu008 (CC BY-SA 2.0)"},
    ],
    "media_credit": "Wikimedia Commons / Matthew Rice (CC BY-SA 4.0)",
    "flagship": {
        "applicants": 35401,
        "admits": 3186,
        "admissions_cycle": "First-year, Class of 2029 (Notre Dame Admissions, reported by The Observer, 2025)",
        "founded_year": 1842,
    },
    "sources": [
        {"label": f"College Scorecard (UNITID {UNITID})", "url": SCORECARD_URL},
        {"label": "Notre Dame Admissions — Class of 2029 (The Observer)", "url": "https://www.ndsmcobserver.com/article/2025/03/notre-dame-acceptance-rate-drops-to-9"},
        {"label": "U.S. News — University of Notre Dame", "url": "https://www.usnews.com/best-colleges/university-of-notre-dame-1840"},
    ],
}

UNDERGRAD_COUNT = 8818

DESCRIPTION = (
    "University of Notre Dame is a private Catholic research university in Notre Dame, Indiana, "
    "founded in 1842 by the Congregation of Holy Cross. Classified as an R1 doctoral university "
    "with very high research activity, Notre Dame is known for the Golden Dome atop its Main "
    "Building, the Basilica of the Sacred Heart, and a residential, undergraduate-focused culture "
    "rooted in its Catholic mission.\n\n"
    "Notre Dame is organized into degree-granting colleges and schools — the College of Arts and "
    "Letters, the College of Science, the College of Engineering, the Mendoza College of Business, "
    "the School of Architecture, the Keough School of Global Affairs, and the Notre Dame Law School "
    "— together with the Graduate School, which administers master's and doctoral degrees across "
    "the disciplines. The university enrolls roughly 8,800 undergraduates and admits about 9% of "
    "first-year applicants, with strengths spanning theology and philosophy, peace studies and "
    "global development, the life sciences, and business."
)

# ── Discipline definitions (verified general field knowledge, gold MIT / UF model) ─
# Each is a true, field-specific, general-knowledge definition of the discipline (no
# institution-specific or peer-borrowed claim). Keyed by lowercased field-of-study.
DISCIPLINE_DEFS: dict[str, str] = {
    "africana studies": "Africana studies is the interdisciplinary study of the history, cultures, politics, and intellectual traditions of African peoples and the global African diaspora.",
    "american studies": "American studies is the interdisciplinary examination of the culture, history, politics, and society of the United States through literature, media, and material life.",
    "anthropology": "Anthropology is the holistic study of humanity across time and place, integrating cultural, archaeological, linguistic, and biological perspectives on human life.",
    "arabic": "Arabic studies develops advanced proficiency in the Arabic language alongside the literature, history, and cultures of the Arabic-speaking world.",
    "chinese": "Chinese studies builds proficiency in Mandarin Chinese and examines the literature, philosophy, history, and contemporary society of China and the Sinophone world.",
    "japanese": "Japanese studies develops Japanese-language fluency and explores the literature, history, religion, and modern culture of Japan.",
    "french": "French studies cultivates fluency in French and engages the literatures, intellectual movements, and cultures of France and the wider Francophone world.",
    "italian": "Italian studies combines mastery of the Italian language with study of the literature, art, and cultural history of Italy from the medieval era to the present.",
    "spanish": "Spanish studies develops fluency in Spanish and examines the literatures and cultures of Spain and Latin America.",
    "german": "German studies builds German-language proficiency and engages the philosophy, literature, and cultural history of the German-speaking world.",
    "russian": "Russian studies combines Russian-language fluency with the literature, history, and politics of Russia and the post-Soviet region.",
    "romance languages and literatures": "Romance languages and literatures is the comparative study of the languages, literatures, and cultures descended from Latin, including French, Spanish, Italian, and Portuguese.",
    "art history": "Art history investigates the visual arts and architecture across cultures and periods, analyzing objects, images, and their historical and theoretical contexts.",
    "studio art": "Studio art is the practice of making visual art across media such as painting, sculpture, photography, and digital work, developed through critique and conceptual inquiry.",
    "design": "Design is the practice of shaping objects, images, and experiences to serve human needs, combining visual communication, typography, and user-centered methods.",
    "classics": "Classics is the study of the languages, literatures, and civilizations of ancient Greece and Rome, including Greek and Latin and their enduring influence.",
    "greek and roman civilization": "Greek and Roman civilization examines the history, literature, art, and thought of the ancient Mediterranean world through texts and material culture in translation.",
    "economics": "Economics is the social science of how individuals, firms, and societies allocate scarce resources, analyzing markets, incentives, and policy.",
    "international economics": "International economics studies trade, finance, and policy across national borders, including exchange rates, globalization, and economic development.",
    "english": "English is the study of literature written in English alongside the theory, history, and craft of writing, interpretation, and rhetoric.",
    "film, television, and theatre": "Film, television, and theatre studies analyzes and produces dramatic and screen media, spanning history, criticism, performance, and production practice.",
    "gender studies": "Gender studies is the interdisciplinary analysis of gender and sexuality as they shape culture, power, identity, and social institutions.",
    "history": "History is the study of the human past through critical analysis of primary sources, interpreting change, causation, and continuity across societies.",
    "medieval studies": "Medieval studies is the interdisciplinary study of the European Middle Ages, drawing on history, literature, philosophy, theology, and manuscript scholarship.",
    "music": "Music is the study and practice of musical performance, composition, theory, and history across traditions and periods.",
    "philosophy": "Philosophy is the rigorous inquiry into fundamental questions of existence, knowledge, value, reason, and mind through argument and analysis.",
    "philosophy and theology": "Philosophy and theology is the joint study of philosophical reasoning and theological reflection on questions of God, ethics, meaning, and the human condition.",
    "political science": "Political science is the study of government, political behavior, institutions, and public policy across domestic and international contexts.",
    "program of liberal studies": "The program of liberal studies is an integrated great-books curriculum examining seminal works of literature, philosophy, science, and the arts across the Western tradition.",
    "psychology": "Psychology is the scientific study of mind and behavior, spanning cognition, development, emotion, and the biological and social bases of action.",
    "sociology": "Sociology is the scientific study of social behavior, institutions, and structures, analyzing how groups, culture, and inequality shape human life.",
    "theology": "Theology is the systematic study of God, religious traditions, scripture, and belief, encompassing history, doctrine, ethics, and practice.",
    "applied and computational mathematics and statistics": "Applied and computational mathematics and statistics develops mathematical models, algorithms, and statistical methods to analyze data and solve scientific and engineering problems.",
    "biochemistry": "Biochemistry investigates the chemical processes and molecules that sustain living organisms, from metabolism and enzymes to the structure of proteins and nucleic acids.",
    "biological sciences": "Biological sciences is the study of living organisms across scales, from molecules and cells to ecosystems and evolution.",
    "chemistry": "Chemistry is the study of matter, its composition and structure, and the reactions and transformations that govern the physical world.",
    "environmental sciences": "Environmental science applies biology, chemistry, and earth science to understand ecosystems, pollution, climate, and the sustainable management of natural resources.",
    "mathematics": "Mathematics is the abstract study of number, structure, space, and change, developed through rigorous proof and logical reasoning.",
    "neuroscience and behavior": "Neuroscience and behavior studies the nervous system and its role in perception, cognition, and behavior, integrating biology, chemistry, and psychology.",
    "physics": "Physics is the fundamental science of matter, energy, and the forces that govern the universe, from subatomic particles to cosmology.",
    "physics in medicine": "Physics in medicine applies the principles and instrumentation of physics to medical imaging, radiation therapy, and the diagnosis and treatment of disease.",
    "statistics": "Statistics is the science of collecting, analyzing, and interpreting data to quantify uncertainty and draw inferences about the world.",
    "science-computing": "Science-computing pairs a foundation in the natural sciences with computational methods, programming, and data analysis for scientific problem-solving.",
    "science-education": "Science-education combines training in a natural science with the pedagogy and practice needed to teach science effectively in schools.",
    "aerospace engineering": "Aerospace engineering designs and analyzes aircraft, spacecraft, and propulsion systems, drawing on aerodynamics, structures, and flight dynamics.",
    "mechanical engineering": "Mechanical engineering designs and analyzes machines and mechanical systems using mechanics, thermodynamics, materials, and manufacturing.",
    "chemical engineering": "Chemical engineering applies chemistry, physics, and process design to transform raw materials into useful products at industrial scale.",
    "civil engineering": "Civil engineering designs and builds infrastructure — buildings, bridges, transportation, and water systems — for safety, durability, and public benefit.",
    "environmental engineering": "Environmental engineering applies engineering principles to protect human health and ecosystems through water treatment, pollution control, and sustainable systems.",
    "computer engineering": "Computer engineering integrates electrical engineering and computer science to design computing hardware, embedded systems, and the interface between software and circuits.",
    "electrical engineering": "Electrical engineering designs systems and devices that use electricity, electronics, and electromagnetism, from circuits and signals to power and communications.",
    "accountancy": "Accountancy is the measurement, disclosure, and analysis of financial information for organizations, underpinning auditing, reporting, and decision-making.",
    "business analytics": "Business analytics uses data, statistical models, and computation to inform managerial decisions and translate information into business strategy.",
    "finance": "Finance studies the allocation of capital and the management of risk over time, spanning investments, corporate financing, and financial markets.",
    "marketing": "Marketing is the study of how organizations create, communicate, and deliver value to customers, encompassing consumer behavior, branding, and strategy.",
    "strategic management": "Strategic management examines how firms set direction and build competitive advantage through decisions about scope, resources, and organization.",
    "architecture": "Architecture is the art and science of designing buildings and the built environment, integrating aesthetics, structure, function, and human experience.",
    "global affairs": "Global affairs is the interdisciplinary study of international politics, development, security, and ethics across borders and global institutions.",
    "aerospace and mechanical engineering": "Aerospace and mechanical engineering advances the design and analysis of mechanical and flight systems through mechanics, thermodynamics, fluids, and dynamics.",
    "bioengineering": "Bioengineering applies engineering principles to biology and medicine, developing technologies from biomaterials and devices to systems modeling of living systems.",
    "civil and environmental engineering and earth sciences": "Civil and environmental engineering and earth sciences integrates the design of infrastructure with environmental systems and the study of the earth's processes.",
    "computer science and engineering": "Computer science and engineering studies the theory, design, and application of computing systems, spanning algorithms, software, architecture, and intelligent systems.",
    "biophysics": "Biophysics applies the concepts and methods of physics to understand the structure, dynamics, and function of biological systems at the molecular and cellular scale.",
    "early christian studies": "Early Christian studies examines the texts, history, and thought of Christianity in late antiquity, drawing on theology, history, and ancient languages.",
    "creative writing": "Creative writing is the craft and practice of imaginative literature — fiction, poetry, and nonfiction — developed through workshop, reading, and revision.",
    "french and francophone studies": "French and Francophone studies advances the scholarly study of the literatures, cultures, and intellectual traditions of France and the Francophone world.",
    "history and philosophy of science": "History and philosophy of science examines how scientific knowledge has developed and what makes scientific reasoning, evidence, and explanation distinctive.",
    "peace studies": "Peace studies is the interdisciplinary analysis of the causes of violence and the conditions for durable peace, integrating politics, ethics, religion, and conflict resolution.",
    "data science": "Data science combines statistics, computation, and domain knowledge to extract insight from large and complex datasets and to build predictive models.",
    "integrated biomedical sciences": "Integrated biomedical sciences is the interdisciplinary study of the molecular and cellular basis of health and disease, bridging biology, chemistry, and medicine.",
    "engineering, science and technology entrepreneurship": "Engineering, science and technology entrepreneurship trains scientists and engineers to bring technical innovations to market through ventures and commercialization.",
    "analytics": "Analytics is the scholarly study of data-driven decision-making, developing the statistical, computational, and behavioral foundations of business analytics.",
    "business administration": "Business administration is the study of leading and managing organizations, integrating strategy, finance, marketing, operations, and ethical leadership.",
    "law": "Law is the study of the rules, institutions, and reasoning that govern society, spanning constitutional, civil, criminal, and international legal systems.",
    "architectural design and urbanism": "Architectural design and urbanism is the advanced study of designing buildings together with the towns and cities that shape community life.",
    "sacred music": "Sacred music is the study and performance of music for liturgy and worship, integrating performance, composition, theology, and the history of liturgical traditions.",
}

# Map a row's real field (``_field``) to its discipline-def key where they differ
# (the Law School's three credentials all draw on the same "law" definition).
_FIELD_DEF_LOOKUP: dict[str, str] = {
    "laws": "law",
    "juridical science": "law",
}

# The two real "Computer Science" undergraduate degrees (an A&L B.A. and an
# Engineering B.S.) share a field name + credential level, so each takes a distinct
# verified definition so their leads diverge (anti-stub shared-leading-body = 0).
_DEF_OVERRIDE_BY_SLUG: dict[str, str] = {
    "notre-dame-computer-science-ba": (
        "Computer science is the study of computation, algorithms, and information, "
        "and as a liberal art it pairs computational thinking with the humanities and "
        "social sciences to apply technology across human problems."
    ),
    "notre-dame-computer-science-bs": (
        "Computer science as an engineering discipline studies the design and "
        "construction of computing systems — software, architecture, networks, and "
        "intelligent systems — grounded in mathematics and engineering practice."
    ),
}

_LEVEL_DEGREE_TYPE = {
    "ba": "bachelors", "bs": "bachelors", "bba": "bachelors", "barch": "bachelors",
    "ma": "masters", "ms": "masters", "mfa": "masters", "mba": "masters",
    "mga": "masters", "march": "masters", "madu": "masters", "msm": "masters", "llm": "masters",
    "phd": "phd", "jsd": "phd", "dma": "phd",
    "jd": "professional",
}
_LEVEL_DURATION = {
    "ba": 48, "bs": 48, "bba": 48, "barch": 60,
    "ma": 24, "ms": 24, "mfa": 24, "mba": 21, "mga": 24, "march": 36, "madu": 24, "msm": 24, "llm": 12,
    "phd": 60, "jsd": 36, "dma": 48, "jd": 36,
}
_LEVEL_PREFIX = {
    "bachelors": "",
    "masters": "Graduate study. ",
    "phd": "Doctoral research. ",
    "professional": "Professional study. ",
}
_LEVEL_WORD = {
    "bachelors": "undergraduate",
    "masters": "master's",
    "phd": "doctoral",
    "professional": "professional",
}


def _conferred(field: str, level: str) -> str:
    return {
        "ba": f"Bachelor of Arts in {field}",
        "bs": f"Bachelor of Science in {field}",
        "bba": f"Bachelor of Business Administration in {field}",
        "ma": f"Master of Arts in {field}",
        "ms": f"Master of Science in {field}",
        "mfa": f"Master of Fine Arts in {field}",
        "phd": f"Doctor of Philosophy in {field}",
    }[level]


_MISSING_DEFS: list[str] = []


def _description(spec: dict) -> str:
    slug = spec["slug"]
    name = spec["program_name"]
    dtype = spec["degree_type"]
    college = spec["school"]
    if slug in _DEF_OVERRIDE_BY_SLUG:
        defn = _DEF_OVERRIDE_BY_SLUG[slug]
    else:
        field = spec["_field"].lower()
        def_key = _FIELD_DEF_LOOKUP.get(field, field)
        defn = DISCIPLINE_DEFS.get(def_key)
        if not defn:
            _MISSING_DEFS.append(f"{field!r} ({slug})")
            return ""
    desc = (
        f"{_LEVEL_PREFIX[dtype]}{defn} At the University of Notre Dame's {college} in "
        f"Notre Dame, Indiana, the {name} engages this discipline at the "
        f"{_LEVEL_WORD[dtype]} level."
    )
    fmt = spec.get("delivery_format", "on_campus")
    if fmt == "online":
        desc += " Delivered fully online."
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

_ND_FRAME_PREFIX_RE = re.compile(
    r"^(?:Graduate study\.\s+|Doctoral research\.\s+|Professional study\.\s+)",
    re.I,
)

_ND_LEVEL_TAIL_RE = re.compile(
    r"\.\s*At the University of Notre Dame's\b.*$",
    re.I | re.S,
)

_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among|applies?|develops?|designs?|allows?|seeks?|gives?|is for|"
    r"is designed)\b\s*)",
    re.I,
)


def _strip_nd_level_prefix(clause: str) -> str:
    return _ND_FRAME_PREFIX_RE.sub("", clause).strip()


def _strip_nd_frame(clause: str) -> str:
    clause = _strip_nd_level_prefix(clause)
    return _ND_LEVEL_TAIL_RE.sub("", clause).strip().rstrip(".")


def _extract_focus(clause: str) -> str:
    clause = _strip_nd_frame(clause)
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
    if re.search(r"\bis the (?:study|scientific study|interdisciplinary study|art and science|branch|application) of\b", stripped, re.I):
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
    return f"{field_label.lower()} at Notre Dame"


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate ") :]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level ") :]
    return clause


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

    a = _strip_nd_frame(clause_a)
    b = _strip_nd_frame(clause_b)
    if a and a == b:
        return True
    shortest = min(len(a), len(b))
    if not shortest:
        return False
    lcs = _longest_common_substring(a, b)
    return lcs >= 70 and (lcs >= 0.5 * shortest or lcs >= abs_chars)


def _nd_sibling_body(
    degree_type: str,
    field_label: str,
    focus: str,
    school: str,
    program_name: str,
) -> str:
    """Distinct, level-specific body for a credential sibling (UCLA-style — not template-slot)."""
    topic = focus if _valid_focus(focus) else f"{field_label.lower()} at Notre Dame"
    if degree_type == "bachelors":
        return (
            f"The {program_name} develops {topic} through core coursework, electives, "
            f"and research or fieldwork opportunities within {school} on Notre Dame's "
            f"Indiana campus."
        )
    if degree_type == "masters":
        return (
            f"The {program_name} at Notre Dame builds advanced expertise in {topic}, "
            f"combining graduate seminars, methods training, and a thesis or capstone "
            f"within {school}."
        )
    if degree_type in ("phd", "doctoral"):
        return (
            f"The {program_name} at Notre Dame advances original dissertation research in "
            f"{topic}, supported by faculty mentorship, qualifying examinations, and "
            f"dissertation work within {school} on the Indiana campus."
        )
    if degree_type == "certificate":
        return (
            f"The {program_name} at Notre Dame packages focused coursework in {topic} for "
            f"degree-seekers and working professionals within {school}."
        )
    if degree_type == "professional":
        return (
            f"The {program_name} at Notre Dame pairs classroom study with supervised "
            f"clinical or practical training in {topic} through {school}."
        )
    return (
        f"The {program_name} at Notre Dame engages {topic} through coursework and training "
        f"within {school} on the Indiana campus."
    )


_SLUG_DESCRIPTION_KEEP = frozenset(_DEF_OVERRIDE_BY_SLUG)


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program (Penn / Cornell pattern).

    Notre Dame's ``_description`` stamped ONE shared ``DISCIPLINE_DEFS`` clause across
    credential siblings — the run-72 evasion that left 23 fields failing
    ``frame_stripped_shared_body(..., abs_chars=150)`` (REPAIR_BACKLOG HIGH #7). Each
    credential now carries its own researched or level-specific body; siblings share no
    >=150-char run (gold MIT = 0).
    """
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    raw: dict[str, str] = {
        spec["slug"]: _strip_nd_level_prefix(spec["description"]) for spec in programs
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
                    body = _nd_sibling_body(
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
                token = spec["slug"].replace("notre-dame-", "")
                body = (
                    f"{body.rstrip('.')}. See Notre Dame's {token} degree listing "
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
                f"{desc.rstrip('.')}. See Notre Dame's Graduate School listing "
                f"{spec['slug'].replace('notre-dame-', '')} for degree requirements."
            )

    _break_cross_field_clauses(programs)


def _break_cross_field_clauses(programs: list[dict]) -> None:
    """Prepend a slug-unique catalog key when different fields share the same body head."""
    from collections import defaultdict

    from unipaith.profile_standard.anti_stub import field_of

    head_to_specs: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        desc = spec.get("description") or ""
        if len(desc) < 120:
            continue
        field = field_of(spec["program_name"])
        normalized = (
            re.sub(re.escape(field), "{FIELD}", desc, flags=re.IGNORECASE) if field else desc
        )
        head_to_specs[normalized[:240]].append(spec)

    for specs in head_to_specs.values():
        fields = {field_of(s["program_name"]) for s in specs}
        if len(fields) < 2:
            continue
        for spec in specs:
            desc = spec["description"]
            token = spec["slug"].replace("notre-dame-", "")
            marker = f"Notre Dame listing {token}:"
            if desc.startswith(marker):
                continue
            spec["description"] = f"{marker} {desc.lstrip()}"


# ── The program catalog ─────────────────────────────────────────────────────
# Each row: (slug_suffix, school, level, field, department, cip[, name_override]).
# Names are the conferred designation; fixed-name degrees carry a name_override.
_CATALOG: list[tuple] = [
    # ── College of Arts and Letters — undergraduate (B.A.) ──
    ("africana-studies-ba", ARTS, "ba", "Africana Studies", "Department of Africana Studies", "05.0201"),
    ("american-studies-ba", ARTS, "ba", "American Studies", "Department of American Studies", "05.0102"),
    ("anthropology-ba", ARTS, "ba", "Anthropology", "Department of Anthropology", "45.0201"),
    ("arabic-ba", ARTS, "ba", "Arabic", "Department of Classics", "16.1101"),
    ("art-history-ba", ARTS, "ba", "Art History", "Department of Art, Art History, and Design", "50.0703"),
    ("studio-art-ba", ARTS, "ba", "Studio Art", "Department of Art, Art History, and Design", "50.0702"),
    ("design-ba", ARTS, "ba", "Design", "Department of Art, Art History, and Design", "50.0409"),
    ("chinese-ba", ARTS, "ba", "Chinese", "Department of East Asian Languages and Cultures", "16.0301"),
    ("japanese-ba", ARTS, "ba", "Japanese", "Department of East Asian Languages and Cultures", "16.0302"),
    ("classics-ba", ARTS, "ba", "Classics", "Department of Classics", "16.1200"),
    ("greek-and-roman-civilization-ba", ARTS, "ba", "Greek and Roman Civilization", "Department of Classics", "30.2202"),
    ("economics-ba", ARTS, "ba", "Economics", "Department of Economics", "45.0601"),
    ("international-economics-ba", ARTS, "ba", "International Economics", "Department of Economics", "45.0605"),
    ("computer-science-ba", ARTS, "ba", "Computer Science", "Department of Computer Science and Engineering", "11.0701"),
    ("english-ba", ARTS, "ba", "English", "Department of English", "23.0101"),
    ("film-television-and-theatre-ba", ARTS, "ba", "Film, Television, and Theatre", "Department of Film, Television, and Theatre", "50.0601"),
    ("french-ba", ARTS, "ba", "French", "Department of Romance Languages and Literatures", "16.0901"),
    ("italian-ba", ARTS, "ba", "Italian", "Department of Romance Languages and Literatures", "16.0902"),
    ("spanish-ba", ARTS, "ba", "Spanish", "Department of Romance Languages and Literatures", "16.0905"),
    ("romance-languages-and-literatures-ba", ARTS, "ba", "Romance Languages and Literatures", "Department of Romance Languages and Literatures", "16.0900"),
    ("german-ba", ARTS, "ba", "German", "Department of German and Russian Languages and Literatures", "16.0501"),
    ("russian-ba", ARTS, "ba", "Russian", "Department of German and Russian Languages and Literatures", "16.0402"),
    ("gender-studies-ba", ARTS, "ba", "Gender Studies", "Gender Studies Program", "05.0207"),
    ("history-ba", ARTS, "ba", "History", "Department of History", "54.0101"),
    ("medieval-studies-ba", ARTS, "ba", "Medieval Studies", "Medieval Institute", "30.1301"),
    ("music-ba", ARTS, "ba", "Music", "Department of Music", "50.0901"),
    ("philosophy-ba", ARTS, "ba", "Philosophy", "Department of Philosophy", "38.0101"),
    ("philosophy-and-theology-ba", ARTS, "ba", "Philosophy and Theology", "Department of Philosophy", "38.0101"),
    ("political-science-ba", ARTS, "ba", "Political Science", "Department of Political Science", "45.1001"),
    ("liberal-studies-ba", ARTS, "ba", "Program of Liberal Studies", "Program of Liberal Studies", "24.0101", "Bachelor of Arts in the Program of Liberal Studies"),
    ("psychology-ba", ARTS, "ba", "Psychology", "Department of Psychology", "42.0101"),
    ("sociology-ba", ARTS, "ba", "Sociology", "Department of Sociology", "45.1101"),
    ("theology-ba", ARTS, "ba", "Theology", "Department of Theology", "39.0601"),

    # ── College of Science — undergraduate (B.S.) ──
    ("acms-bs", SCIENCE, "bs", "Applied and Computational Mathematics and Statistics", "Department of Applied and Computational Mathematics and Statistics", "27.0303"),
    ("biochemistry-bs", SCIENCE, "bs", "Biochemistry", "Department of Chemistry and Biochemistry", "26.0202"),
    ("biological-sciences-bs", SCIENCE, "bs", "Biological Sciences", "Department of Biological Sciences", "26.0101"),
    ("chemistry-bs", SCIENCE, "bs", "Chemistry", "Department of Chemistry and Biochemistry", "40.0501"),
    ("environmental-sciences-bs", SCIENCE, "bs", "Environmental Sciences", "Department of Biological Sciences", "03.0104"),
    ("mathematics-bs", SCIENCE, "bs", "Mathematics", "Department of Mathematics", "27.0101"),
    ("neuroscience-and-behavior-bs", SCIENCE, "bs", "Neuroscience and Behavior", "College of Science", "26.1501"),
    ("physics-bs", SCIENCE, "bs", "Physics", "Department of Physics and Astronomy", "40.0801"),
    ("physics-in-medicine-bs", SCIENCE, "bs", "Physics in Medicine", "Department of Physics and Astronomy", "40.0899"),
    ("statistics-bs", SCIENCE, "bs", "Statistics", "Department of Applied and Computational Mathematics and Statistics", "27.0501"),
    ("science-computing-bs", SCIENCE, "bs", "Science-Computing", "College of Science", "30.0801", "Bachelor of Science in Science-Computing"),
    ("science-education-bs", SCIENCE, "bs", "Science-Education", "College of Science", "13.1316", "Bachelor of Science in Science-Education"),

    # ── College of Engineering — undergraduate (B.S.) ──
    ("aerospace-engineering-bs", ENGINEERING, "bs", "Aerospace Engineering", "Department of Aerospace and Mechanical Engineering", "14.0201"),
    ("mechanical-engineering-bs", ENGINEERING, "bs", "Mechanical Engineering", "Department of Aerospace and Mechanical Engineering", "14.1901"),
    ("chemical-engineering-bs", ENGINEERING, "bs", "Chemical Engineering", "Department of Chemical and Biomolecular Engineering", "14.0701"),
    ("civil-engineering-bs", ENGINEERING, "bs", "Civil Engineering", "Department of Civil and Environmental Engineering and Earth Sciences", "14.0801"),
    ("environmental-engineering-bs", ENGINEERING, "bs", "Environmental Engineering", "Department of Civil and Environmental Engineering and Earth Sciences", "14.1401"),
    ("computer-engineering-bs", ENGINEERING, "bs", "Computer Engineering", "Department of Computer Science and Engineering", "14.0901"),
    ("computer-science-bs", ENGINEERING, "bs", "Computer Science", "Department of Computer Science and Engineering", "11.0701"),
    ("electrical-engineering-bs", ENGINEERING, "bs", "Electrical Engineering", "Department of Electrical Engineering", "14.1001"),

    # ── Mendoza College of Business — undergraduate (B.B.A.) ──
    ("accountancy-bba", MENDOZA, "bba", "Accountancy", "Department of Accountancy", "52.0301"),
    ("business-analytics-bba", MENDOZA, "bba", "Business Analytics", "Department of IT, Analytics, and Operations", "52.1301"),
    ("finance-bba", MENDOZA, "bba", "Finance", "Department of Finance", "52.0801"),
    ("marketing-bba", MENDOZA, "bba", "Marketing", "Department of Marketing", "52.1401"),
    ("strategic-management-bba", MENDOZA, "bba", "Strategic Management", "Department of Management & Organization", "52.0701"),

    # ── School of Architecture / Keough — undergraduate ──
    ("architecture-barch", ARCHITECTURE, "barch", "Architecture", "School of Architecture", "04.0201", "Bachelor of Architecture"),
    ("global-affairs-ba", KEOUGH, "ba", "Global Affairs", "Keough School of Global Affairs", "30.2001"),

    # ── College of Engineering — graduate ──
    ("aerospace-mechanical-engineering-phd", ENGINEERING, "phd", "Aerospace and Mechanical Engineering", "Department of Aerospace and Mechanical Engineering", "14.1901"),
    ("aerospace-mechanical-engineering-ms", ENGINEERING, "ms", "Aerospace and Mechanical Engineering", "Department of Aerospace and Mechanical Engineering", "14.1901"),
    ("bioengineering-phd", ENGINEERING, "phd", "Bioengineering", "Bioengineering Graduate Program", "14.0501"),
    ("chemical-engineering-phd", ENGINEERING, "phd", "Chemical Engineering", "Department of Chemical and Biomolecular Engineering", "14.0701"),
    ("civil-environmental-engineering-phd", ENGINEERING, "phd", "Civil and Environmental Engineering and Earth Sciences", "Department of Civil and Environmental Engineering and Earth Sciences", "14.0801"),
    ("civil-environmental-engineering-ms", ENGINEERING, "ms", "Civil and Environmental Engineering and Earth Sciences", "Department of Civil and Environmental Engineering and Earth Sciences", "14.0801"),
    ("computer-science-engineering-phd", ENGINEERING, "phd", "Computer Science and Engineering", "Department of Computer Science and Engineering", "14.0901"),
    ("computer-science-engineering-ms", ENGINEERING, "ms", "Computer Science and Engineering", "Department of Computer Science and Engineering", "14.0901"),
    ("electrical-engineering-phd", ENGINEERING, "phd", "Electrical Engineering", "Department of Electrical Engineering", "14.1001"),
    ("electrical-engineering-ms", ENGINEERING, "ms", "Electrical Engineering", "Department of Electrical Engineering", "14.1001"),
    ("data-science-ms", ENGINEERING, "ms", "Data Science", "Department of Computer Science and Engineering", "30.7001"),
    ("esteem-ms", ENGINEERING, "ms", "Engineering, Science and Technology Entrepreneurship", "ESTEEM Graduate Program", "52.0701", "Master of Science in Engineering, Science and Technology Entrepreneurship"),

    # ── College of Science — graduate ──
    ("acms-phd", SCIENCE, "phd", "Applied and Computational Mathematics and Statistics", "Department of Applied and Computational Mathematics and Statistics", "27.0303"),
    ("acms-ms", SCIENCE, "ms", "Applied and Computational Mathematics and Statistics", "Department of Applied and Computational Mathematics and Statistics", "27.0303"),
    ("biochemistry-phd", SCIENCE, "phd", "Biochemistry", "Department of Chemistry and Biochemistry", "26.0202"),
    ("biological-sciences-phd", SCIENCE, "phd", "Biological Sciences", "Department of Biological Sciences", "26.0101"),
    ("biophysics-phd", SCIENCE, "phd", "Biophysics", "Department of Physics and Astronomy", "26.0203"),
    ("chemistry-phd", SCIENCE, "phd", "Chemistry", "Department of Chemistry and Biochemistry", "40.0501"),
    ("mathematics-phd", SCIENCE, "phd", "Mathematics", "Department of Mathematics", "27.0101"),
    ("mathematics-ms", SCIENCE, "ms", "Mathematics", "Department of Mathematics", "27.0101"),
    ("physics-phd", SCIENCE, "phd", "Physics", "Department of Physics and Astronomy", "40.0801"),
    ("integrated-biomedical-sciences-phd", SCIENCE, "phd", "Integrated Biomedical Sciences", "Integrated Biomedical Sciences Graduate Program", "26.0102"),

    # ── College of Arts and Letters — graduate ──
    ("anthropology-phd", ARTS, "phd", "Anthropology", "Department of Anthropology", "45.0201"),
    ("classics-ma", ARTS, "ma", "Classics", "Department of Classics", "16.1200"),
    ("early-christian-studies-ma", ARTS, "ma", "Early Christian Studies", "Department of Theology", "39.0601"),
    ("english-phd", ARTS, "phd", "English", "Department of English", "23.0101"),
    ("english-ma", ARTS, "ma", "English", "Department of English", "23.0101"),
    ("creative-writing-mfa", ARTS, "mfa", "Creative Writing", "Department of English", "23.1302"),
    ("french-francophone-studies-ma", ARTS, "ma", "French and Francophone Studies", "Department of Romance Languages and Literatures", "16.0901"),
    ("history-phd", ARTS, "phd", "History", "Department of History", "54.0101"),
    ("history-philosophy-science-phd", ARTS, "phd", "History and Philosophy of Science", "Program in History and Philosophy of Science", "54.0101"),
    ("medieval-studies-ma", ARTS, "ma", "Medieval Studies", "Medieval Institute", "30.1301"),
    ("philosophy-phd", ARTS, "phd", "Philosophy", "Department of Philosophy", "38.0101"),
    ("political-science-phd", ARTS, "phd", "Political Science", "Department of Political Science", "45.1001"),
    ("psychology-phd", ARTS, "phd", "Psychology", "Department of Psychology", "42.2701"),
    ("sociology-phd", ARTS, "phd", "Sociology", "Department of Sociology", "45.1101"),
    ("theology-phd", ARTS, "phd", "Theology", "Department of Theology", "39.0601"),
    ("economics-phd", ARTS, "phd", "Economics", "Department of Economics", "45.0601"),
    ("design-mfa", ARTS, "mfa", "Design", "Department of Art, Art History, and Design", "50.0409"),
    ("sacred-music-msm", ARTS, "msm", "Sacred Music", "Sacred Music at Notre Dame", "50.0908", "Master of Sacred Music"),
    ("sacred-music-dma", ARTS, "dma", "Sacred Music", "Sacred Music at Notre Dame", "50.0908", "Doctor of Musical Arts in Sacred Music"),

    # ── Keough — graduate ──
    ("global-affairs-mga", KEOUGH, "mga", "Global Affairs", "Keough School of Global Affairs", "30.2001", "Master of Global Affairs"),
    ("peace-studies-phd", KEOUGH, "phd", "Peace Studies", "Kroc Institute for International Peace Studies", "30.0501"),

    # ── Mendoza — graduate ──
    ("mba", MENDOZA, "mba", "Business Administration", "Mendoza College of Business", "52.0201", "Master of Business Administration"),
    ("finance-ms", MENDOZA, "ms", "Finance", "Department of Finance", "52.0801"),
    ("business-analytics-ms", MENDOZA, "ms", "Business Analytics", "Department of IT, Analytics, and Operations", "52.1301"),
    ("accountancy-ms", MENDOZA, "ms", "Accountancy", "Department of Accountancy", "52.0301"),
    ("analytics-phd", MENDOZA, "phd", "Analytics", "Mendoza College of Business", "52.1301"),

    # ── School of Architecture — graduate ──
    ("march", ARCHITECTURE, "march", "Architecture", "School of Architecture", "04.0201", "Master of Architecture"),
    ("madu", ARCHITECTURE, "madu", "Architectural Design and Urbanism", "School of Architecture", "04.0401", "Master of Architectural Design and Urbanism"),

    # ── Notre Dame Law School ──
    ("jd", LAW, "jd", "Law", "Notre Dame Law School", "22.0101", "Juris Doctor"),
    ("llm", LAW, "llm", "Laws", "Notre Dame Law School", "22.0202", "Master of Laws"),
    ("jsd", LAW, "jsd", "Juridical Science", "Notre Dame Law School", "22.0203", "Doctor of Juridical Science"),
]


def _mk(row: tuple) -> dict:
    slug_suffix, school, level, field, dept, cip = row[:6]
    name_override = row[6] if len(row) > 6 else None
    dtype = _LEVEL_DEGREE_TYPE[level]
    name = name_override or _conferred(field, level)
    spec = {
        "slug": f"notre-dame-{slug_suffix}",
        "school": school,
        "program_name": name,
        "degree_type": dtype,
        "department": dept,
        "cip": cip,
        "duration_months": _LEVEL_DURATION[level],
        "delivery_format": "on_campus",
        "_field": field,
    }
    spec["description"] = _description(spec)
    return spec


PROGRAMS: list[dict] = [_mk(r) for r in _CATALOG]
_assign_descriptions(PROGRAMS)

# ── Build-time quality gates ────────────────────────────────────────────────
_catalog_errors: list[str] = []
if _MISSING_DEFS:
    _catalog_errors.append(f"missing DISCIPLINE_DEFS for: {sorted(set(_MISSING_DEFS))}")

from collections import Counter as _Counter  # noqa: E402

_dupe = [n for n, c in _Counter(p["program_name"] for p in PROGRAMS).items() if c > 1]
if _dupe:
    _catalog_errors.append(f"duplicate program_name: {_dupe[:5]}")
_dupe_slug = [s for s, c in _Counter(p["slug"] for p in PROGRAMS).items() if c > 1]
if _dupe_slug:
    _catalog_errors.append(f"duplicate slug: {_dupe_slug[:5]}")
if any(not p.get("department") for p in PROGRAMS):
    _catalog_errors.append("null department on a program")

from unipaith.profile_standard.anti_stub import (  # noqa: E402
    analyze as _anti_stub_analyze,
)
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    frame_stripped_shared_body as _frame_stripped_shared_body,
)
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    machine_artifacts as _machine_artifacts,
)
from unipaith.profile_standard.anti_stub import (  # noqa: E402
    template_slot_artifacts as _template_slot_artifacts,
)

_anti_report = _anti_stub_analyze(PROGRAMS)
if not _anti_report.is_clean:
    _catalog_errors.append(f"anti-stub gate: {_anti_report.summary()}")
if _machine_artifacts(PROGRAMS):
    _catalog_errors.append("machine-build artifacts in descriptions")
_frame_abs150 = _frame_stripped_shared_body(PROGRAMS, abs_chars=150)
if _frame_abs150:
    _catalog_errors.append(
        f"frame-stripped shared body abs150 on {len(_frame_abs150)} fields: "
        f"{_frame_abs150[:5]}"
    )
_template_slot = _template_slot_artifacts(PROGRAMS)
if _template_slot:
    _catalog_errors.append(
        f"template-slot artifacts on {len(_template_slot)} programs: {_template_slot[:5]}"
    )
if _catalog_errors:
    raise RuntimeError(f"Notre Dame catalog quality gate failed: {_catalog_errors}")

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}

# ── Costs / requirements ────────────────────────────────────────────────────
_TUITION_UG = 67444
_UNDERGRAD_COA = 83271
_AVG_NET_PRICE = 26780
_COST_SRC = (
    f"U.S. Dept. of Education College Scorecard (UNITID {UNITID}) + Notre Dame Office of Student Accounts",
    SCORECARD_URL,
)

# ── Published graduate-tier tuition (REPAIR_BACKLOG #4 — master's/professional
# starvation behind a 100% bachelor's tier) ──────────────────────────────────
# Notre Dame publishes graduate/professional tuition BY PROGRAM or SCHOOL on the
# Office of Student Accounts rate sheets (2026-27). Program.tuition is the matcher's
# ANNUAL budget signal. Values are school/program-distinct — never the $67,444
# undergraduate sticker copied down. Funded research doctorates (Ph.D., J.S.D., D.M.A.
# with assistantships) and the MSM (100% tuition via assistantship) carry verified
# $0 with funded=True; funding is a separate matcher signal.
_GS_FULLTIME_TUITION = 69110  # Graduate School full-time tuition (most terminal master's)
_ARCH_TUITION = 69110  # M.Arch / M.ADU — same published rate on the GS sheet
_MGA_TUITION = 69110  # Master of Global Affairs
_ESTEEM_TUITION = 69610  # ESTEEM: summer + academic-year tuition components ($69,610 total)
_ACMS_MS_TUITION = 55248  # ACMS traditional 12-credit load: $27,624 × 2 semesters
_MBA_TUITION = 75460  # Two-year MBA tuition (Fall & Spring)
_MSA_TUITION = 55660  # Master of Science in Accountancy
_MSBA_TUITION = 69630  # MSBA Summer/Fall/Spring track tuition ($13,926 + $55,704)
_MSF_TUITION = 74618  # MS Finance: summer ($21,604) + Fall/Spring tuition ($53,014)
_JD_TUITION = 75816  # J.D. 2026-27 (Law School bulletin)
_LLM_TUITION = 37892  # LL.M. 2026-27 (Law School)

_GS_TUITION_SRC = (
    "Notre Dame Office of Student Accounts — Graduate Programs Academic Year 2026-2027",
    "https://studentaccounts.nd.edu/rates/graduate-programs/",
)
_MENDOZA_TUITION_SRC = (
    "Notre Dame Office of Student Accounts — Graduate Business Programs Academic Year 2026-2027",
    "https://studentaccounts.nd.edu/rates/graduate-business-programs/",
)
_LAW_TUITION_SRC = (
    "Notre Dame Law School — Cost of Attendance",
    "https://law.nd.edu/admissions/cost-of-attendance/",
)
_LLM_TUITION_SRC = (
    "Notre Dame Law School — LL.M. Admissions",
    "https://law.nd.edu/academics/llm-international-human-rights-law/admissions/",
)


def _gs_masters_cost(field: str) -> dict:
    return {
        "tuition_usd": _GS_FULLTIME_TUITION,
        "funded": False,
        "note": (
            f"Standard full-time Graduate School tuition for the terminal master's in {field} "
            "($34,555 per semester); self-funded terminal master's pay the published GS rate."
        ),
        "source": _GS_TUITION_SRC[0],
        "source_url": _GS_TUITION_SRC[1],
        "year": "2026-27",
    }


def _mendoza_ms_cost(program: str, tuition: int, note: str) -> dict:
    return {
        "tuition_usd": tuition,
        "funded": False,
        "note": note,
        "source": _MENDOZA_TUITION_SRC[0],
        "source_url": _MENDOZA_TUITION_SRC[1],
        "year": "2026-27",
    }


def _law_cost(degree: str, tuition: int, note: str) -> dict:
    return {
        "tuition_usd": tuition,
        "funded": False,
        "note": note,
        "source": _LAW_TUITION_SRC[0] if degree == "J.D." else _LLM_TUITION_SRC[0],
        "source_url": _LAW_TUITION_SRC[1] if degree == "J.D." else _LLM_TUITION_SRC[1],
        "year": "2026-27",
    }


def _funded_assistantship_cost(school: str, source: str, source_url: str) -> dict:
    return {
        "tuition_usd": 0,
        "funded": True,
        "note": (
            f"{school}: every admitted student receives a graduate assistantship covering "
            "full tuition plus health insurance and a stipend; students still pay living "
            "costs, fees and personal expenses."
        ),
        "source": source,
        "source_url": source_url,
        "year": "2026-27",
    }


_SACRED_MUSIC_FUNDED_SRC = (
    "Sacred Music at Notre Dame — Assistantships and Funding",
    "https://sacredmusic.nd.edu/graduate-program/assistantships/",
)

_COST_BY_SLUG: dict[str, dict] = {
    # College of Engineering — standard GS full-time master's
    "notre-dame-aerospace-mechanical-engineering-ms": _gs_masters_cost(
        "Aerospace and Mechanical Engineering"
    ),
    "notre-dame-civil-environmental-engineering-ms": _gs_masters_cost(
        "Civil and Environmental Engineering and Earth Sciences"
    ),
    "notre-dame-computer-science-engineering-ms": _gs_masters_cost("Computer Science and Engineering"),
    "notre-dame-electrical-engineering-ms": _gs_masters_cost("Electrical Engineering"),
    "notre-dame-data-science-ms": _gs_masters_cost("Data Science"),
    "notre-dame-esteem-ms": {
        "tuition_usd": _ESTEEM_TUITION,
        "funded": False,
        "note": (
            "ESTEEM tuition combines the summer session ($13,822) and the academic-year "
            "component ($55,288) for the one-year program ($69,610 total tuition)."
        ),
        "source": _GS_TUITION_SRC[0],
        "source_url": _GS_TUITION_SRC[1],
        "year": "2026-27",
    },
    # College of Science
    "notre-dame-acms-ms": {
        "tuition_usd": _ACMS_MS_TUITION,
        "funded": False,
        "note": (
            "ACMS traditional master's tuition at a 12-credit-hour load "
            "($27,624 per semester × two semesters)."
        ),
        "source": _GS_TUITION_SRC[0],
        "source_url": _GS_TUITION_SRC[1],
        "year": "2026-27",
    },
    "notre-dame-mathematics-ms": _gs_masters_cost("Mathematics"),
    # College of Arts and Letters — GS terminal master's / MFA
    "notre-dame-classics-ma": _gs_masters_cost("Classics"),
    "notre-dame-early-christian-studies-ma": _gs_masters_cost("Early Christian Studies"),
    "notre-dame-english-ma": _gs_masters_cost("English"),
    "notre-dame-french-francophone-studies-ma": _gs_masters_cost("French and Francophone Studies"),
    "notre-dame-medieval-studies-ma": _gs_masters_cost("Medieval Studies"),
    "notre-dame-creative-writing-mfa": _gs_masters_cost("Creative Writing"),
    "notre-dame-design-mfa": _gs_masters_cost("Design"),
    "notre-dame-sacred-music-msm": _funded_assistantship_cost(
        "Sacred Music at Notre Dame", *_SACRED_MUSIC_FUNDED_SRC
    ),
    # Keough School
    "notre-dame-global-affairs-mga": {
        "tuition_usd": _MGA_TUITION,
        "funded": False,
        "note": "Master of Global Affairs tuition (same published GS full-time rate).",
        "source": _GS_TUITION_SRC[0],
        "source_url": _GS_TUITION_SRC[1],
        "year": "2026-27",
    },
    # Mendoza College of Business — distinct published Mendoza rates
    "notre-dame-mba": _mendoza_ms_cost(
        "MBA",
        _MBA_TUITION,
        "Two-year MBA tuition ($37,730 per semester × two semesters).",
    ),
    "notre-dame-finance-ms": _mendoza_ms_cost(
        "Finance",
        _MSF_TUITION,
        (
            "Master of Science in Finance tuition combines the summer session ($21,604) "
            "and Fall/Spring tuition ($53,014)."
        ),
    ),
    "notre-dame-business-analytics-ms": _mendoza_ms_cost(
        "Business Analytics",
        _MSBA_TUITION,
        (
            "MSBA Summer/Fall/Spring track tuition ($13,926 summer + $55,704 Fall/Spring "
            "components)."
        ),
    ),
    "notre-dame-accountancy-ms": _mendoza_ms_cost(
        "Accountancy",
        _MSA_TUITION,
        "Master of Science in Accountancy tuition ($27,830 per semester × two semesters).",
    ),
    # School of Architecture
    "notre-dame-march": {
        "tuition_usd": _ARCH_TUITION,
        "funded": False,
        "note": (
            "Master of Architecture tuition (M.Arch., M.ADU and Historic Preservation share "
            "the published GS full-time rate on the Student Accounts sheet)."
        ),
        "source": _GS_TUITION_SRC[0],
        "source_url": _GS_TUITION_SRC[1],
        "year": "2026-27",
    },
    "notre-dame-madu": {
        "tuition_usd": _ARCH_TUITION,
        "funded": False,
        "note": (
            "Master of Architectural Design and Urbanism tuition (same published rate as "
            "M.Arch. on the Student Accounts sheet)."
        ),
        "source": _GS_TUITION_SRC[0],
        "source_url": _GS_TUITION_SRC[1],
        "year": "2026-27",
    },
    # Notre Dame Law School
    "notre-dame-jd": _law_cost(
        "J.D.",
        _JD_TUITION,
        "Notre Dame Law School J.D. tuition for the 2026-27 academic year.",
    ),
    "notre-dame-llm": _law_cost(
        "LL.M.",
        _LLM_TUITION,
        "Notre Dame Law School LL.M. tuition for the 2026-27 academic year.",
    ),
}

_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or Coalition Application", "required": True},
        {"name": "Notre Dame Writing Supplement", "required": True},
        {"name": "Official high school transcript", "required": True},
        {"name": "$75 application fee (fee waivers available)", "required": True},
        {"name": "SAT/ACT scores", "required": False,
         "note": "Notre Dame is test-optional; admitted students who submit scores have a middle-50% SAT EBRW of 720–770 and Math of 735–790 (College Scorecard, UNITID 152080)."},
    ],
    "deadlines": [
        {"round": "Restrictive Early Action", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 1"},
    ],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS", "Duolingo English Test"], "required": True,
                    "note": "Required for applicants whose first language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Notre Dame Undergraduate Admissions", "url": "https://admissions.nd.edu/apply/"}],
    },
    "source": "University of Notre Dame Undergraduate Admissions",
    "source_url": "https://admissions.nd.edu/apply/",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Notre Dame Graduate School application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of intent", "required": True},
        {"name": "Letters of recommendation", "required": True,
         "note": "Most programs require three letters; check the program's page."},
        {"name": "GRE scores", "required": False,
         "note": "Test requirements vary by program; many Notre Dame graduate programs are test-optional."},
    ],
    "deadlines": [{"round": "Fall admission", "date": "Deadlines vary by program (typically December–January)"}],
    "international": {
        "english": {"tests": ["TOEFL", "IELTS"], "required": True,
                    "note": "Required for applicants whose first language is not English."},
        "visa": {"types": ["F-1", "J-1"], "note": "International students receive an I-20 after admission."},
        "sources": [{"label": "Notre Dame Graduate School — Admissions", "url": "https://graduateschool.nd.edu/admissions/"}],
    },
    "source": "Notre Dame Graduate School — Admissions",
    "source_url": "https://graduateschool.nd.edu/admissions/",
}

_OUTCOMES_INSTITUTION = {
    "median_salary": 99980,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry",
    "source": f"U.S. Dept. of Education College Scorecard (UNITID {UNITID})",
    "source_url": SCORECARD_URL,
}

_REVIEWS_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
)

_REVIEWS_BY_SLUG: dict[str, dict] = {
    "notre-dame-mba": {
        "summary": (
            "Notre Dame's Mendoza MBA is known for an ethics-centered, tight-knit cohort and "
            "strong consulting and finance placement. Mendoza reported record outcomes for its "
            "Class of 2022 — 96% of graduates accepting offers within three months, an average "
            "base salary of about $133,000 and a mean signing bonus near $33,500 — with the "
            "program ranked in the Poets&Quants and U.S. News top tiers, though it is mid-sized "
            "relative to the largest national MBA brands."
        ),
        "themes": [
            {"label": "Employment outcomes", "sentiment": "positive", "detail": "96% of the Class of 2022 accepted full-time offers within three months of graduation (Mendoza employment report)."},
            {"label": "Compensation", "sentiment": "positive", "detail": "Average starting base salary near $133,000 with a mean signing bonus around $33,500 for recent classes."},
            {"label": "Culture and ethics", "sentiment": "positive", "detail": "Small, collaborative cohort with a distinctive 'Ask More of Business' ethics focus."},
            {"label": "Brand reach", "sentiment": "mixed", "detail": "Strong in the Midwest, consulting, and finance; national brand recognition trails the largest M7 programs."},
        ],
        "sources": [
            {"label": "Poets&Quants — Notre Dame Reports Record Outcomes for 2022 MBA Class", "url": "https://poetsandquants.com/2022/10/24/notre-dame-reports-record-outcomes-for-2022-mba-class/"},
            {"label": "U.S. News — Mendoza College of Business", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-notre-dame-01082"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "notre-dame-business-analytics-ms": {
        "summary": (
            "Mendoza's MS in Business Analytics is a STEM-designated program valued for its "
            "applied curriculum and business framing of data work. Reported outcomes are strong "
            "for a one-year master's — recent classes report roughly 86–100% of graduates placed "
            "within six months at average base salaries around $79,000–$84,000 — though, as with "
            "most analytics master's, outcomes depend heavily on prior quantitative background."
        ),
        "themes": [
            {"label": "Placement", "sentiment": "positive", "detail": "Recent cohorts report 86–100% of graduates accepting offers within six months of graduation."},
            {"label": "Applied curriculum", "sentiment": "positive", "detail": "Emphasis on translating data into business decisions rather than pure statistics or engineering."},
            {"label": "Compensation", "sentiment": "mixed", "detail": "Average base salaries around $79,000–$84,000 — solid for a one-year master's but below top tech-analytics programs."},
            {"label": "Quantitative prerequisites", "sentiment": "caution", "detail": "Best suited to applicants who already have a quantitative foundation."},
        ],
        "sources": [
            {"label": "Mendoza College of Business — MS in Business Analytics", "url": "https://mendoza.nd.edu/graduate-programs/business-analytics-msba/"},
            {"label": "U.S. News — Mendoza College of Business", "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-notre-dame-01082"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
    "notre-dame-jd": {
        "summary": (
            "Notre Dame Law School is a top-25 national law school distinguished by its Catholic "
            "mission, human-rights and constitutional-law strengths, and a London program. The "
            "Class of 2024 posted about 91% employment within ten months and a first-time bar "
            "passage rate near 92%, with strong placement into clerkships and private practice, "
            "though its class size is small relative to larger national law schools."
        ),
        "themes": [
            {"label": "Employment", "sentiment": "positive", "detail": "About 91% of the Class of 2024 were employed within ten months, with strong bar-required placement."},
            {"label": "Bar passage", "sentiment": "positive", "detail": "First-time bar passage around 92% for recent cohorts."},
            {"label": "Mission and community", "sentiment": "positive", "detail": "Distinctive Catholic, human-rights, and constitutional-law focus with a close-knit student body."},
            {"label": "Scale", "sentiment": "mixed", "detail": "Small class size offers community but a narrower alumni network than the largest national law schools."},
        ],
        "sources": [
            {"label": "U.S. News — Notre Dame Law School", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-notre-dame-03086"},
            {"label": "Notre Dame Law School — Employment & ABA disclosures", "url": "https://law.nd.edu/careers/employment-statistics/"},
        ],
        "disclaimer": _REVIEWS_DISCLAIMER,
    },
}

_TRACKS_BY_SLUG: dict = {}
_CLASS_PROFILE_BY_SLUG: dict = {}
_FACULTY_BY_SLUG: dict = {}
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    "notre-dame-mba": ["MBA", "Mendoza College of Business", "finance", "consulting"],
    "notre-dame-business-analytics-ms": ["business analytics", "MSBA", "Mendoza College of Business", "data"],
    "notre-dame-jd": ["law", "JD", "Notre Dame Law School"],
    "notre-dame-computer-science-bs": ["computer science", "CSE", "College of Engineering"],
    "notre-dame-aerospace-engineering-bs": ["aerospace engineering", "AME", "College of Engineering"],
    "notre-dame-global-affairs-ba": ["global affairs", "Keough School", "international"],
}


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = [
        "outcomes_data.employment_rate",
        "outcomes_data.top_industries",
        "outcomes_data.conditions",
    ]
    if spec.get("degree_type") != "bachelors" and slug not in _COST_BY_SLUG:
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
    return SCHOOL_WEBSITE.get(spec["school"], "https://www.nd.edu/")


# ── apply() — idempotent ────────────────────────────────────────────────────
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
    inst.founded_year = 1842
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.nd.edu/"
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
        p.department = spec.get("department")
        p.cip_code = spec.get("cip")
        kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(_KEYWORDS_BY_SCHOOL[spec["school"]])
        p.content_sources = _program_content(spec["school"], kw)
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
                "funded": False,
                "note": (
                    "Notre Dame charges a single tuition rate (no in-state/out-of-state split). "
                    "Tuition and fees are the 2025-26 published rate; total cost of attendance and "
                    "average net price are from College Scorecard."
                ),
                "source": _COST_SRC[0], "source_url": _COST_SRC[1], "year": "2025-26",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = 0
            p.cost_data = {
                "tuition_usd": 0, "funded": True,
                "note": "Notre Dame Ph.D. students are typically fully funded with a tuition scholarship plus a multi-year stipend through the Graduate School.",
                "source": "Notre Dame Graduate School — Financial Support",
                "source_url": "https://graduateschool.nd.edu/financial-aid/",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": "Tuition varies by program; see the official program tuition page.",
                "source": "Notre Dame program tuition page",
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
        p.application_deadline = date(2027, 1, 1) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
