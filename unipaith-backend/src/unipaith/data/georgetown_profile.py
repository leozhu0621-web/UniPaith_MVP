"""Georgetown University — canonical profile data (enrich-profile routine).

Built from the gold reference shape in ``mit_profile.py`` / ``dartmouth_profile.py``.
Every value is verified against an authoritative source and carries a citation in the
node's ``sources`` / per-field note; anything unverifiable is recorded in
``_standard.omitted`` rather than guessed (the one inviolable rule).

Institution stats: U.S. Dept. of Education College Scorecard + NCES College Navigator
(UNITID 131496) + Georgetown Office of Institutional Research Common Data Set.
Catalog: Georgetown University Bulletin (bulletin.georgetown.edu) + the official
school sites, cross-checked against the IPEDS / College Scorecard CIP program list.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models import Institution, Program, School
from unipaith.profile_standard.manifest import STANDARD_VERSION

INSTITUTION_NAME = "Georgetown University"
ENRICHED_AT = "2026-06-25"


def _standard(omitted: list[str] | None = None) -> dict:
    return {"version": STANDARD_VERSION, "enriched_at": ENRICHED_AT, "omitted": omitted or []}


# Institution-level required fields with no citable source this session — honestly
# omitted rather than guessed.
_OMITTED_INSTITUTION: list[str] = [
    # Georgetown publishes a student-faculty ratio (below) but no single current
    # instructional-faculty headcount could be verified, so the count is omitted.
    "school_outcomes.scale.faculty_count",
    # Georgetown publishes no single university-wide first-destination outcome rate or
    # employer-industry breakdown across all schools, so these institution-level rollups
    # are omitted (per-program outcomes carry the College Scorecard earnings instead).
    "school_outcomes.employed_or_continuing_ed",
    "school_outcomes.top_employer_industries",
]

# ── Institution-level data ────────────────────────────────────────────────
RANKING_DATA: dict = {
    "ownership_type": "private",
    # Georgetown's institutional accreditor.
    "accreditor": "Middle States Commission on Higher Education",
    # Carnegie 2025 basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    # QS World University Rankings 2026.
    "qs_world_university_rankings": {"rank": 285, "year": 2026},
    # Times Higher Education World University Rankings 2025.
    "times_higher_education": {"rank": 201, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2025: #24 nationally.
    "us_news_national": {"rank": 24, "year": 2026},
}

# school_outcomes is shallow-merged into the federal seed JSONB (which already wrote
# admit_rate / avg_net_price / median_earnings_10yr / location / campus_photos).
SCHOOL_OUTCOMES: dict = {
    # College Scorecard (federal seed) — first-year admit rate.
    "admit_rate": 0.1291,
    "avg_net_price": 40815,
    "median_earnings_10yr": 103494,
    # NCES College Navigator / College Scorecard six-year graduation rate.
    "graduation_rate_6yr": 0.95,
    # NCES College Navigator: first-year retention.
    "retention_rate_first_year": 0.97,
    "financial_aid": {
        # Georgetown Office of Student Financial Aid — 2025-26 first-year total COA.
        "cost_of_attendance": 96492,
        # NCES College Navigator (IPEDS) — share of undergraduates receiving Pell grants.
        "pell_grant_rate": 0.11,
    },
    # Undergraduate race/ethnicity (NCES College Navigator, IPEDS fall 2024, CDS-derived).
    "demographics": {
        "white": 0.45,
        "asian": 0.15,
        "international": 0.14,
        "unknown": 0.09,
        "hispanic": 0.06,
        "two_or_more": 0.06,
        "black": 0.05,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (CDS 2024-25 / NCES components).
    "test_scores": {
        "sat_total_25_75": [1400, 1540],
        "act_25_75": [31, 35],
    },
    # Georgetown main campus, Washington, DC.
    "location": {"lat": 38.90722, "lng": -77.07278, "source": "Wikipedia / Wikidata"},
    "campus_basics": {"location": "Washington, District of Columbia"},
    "scale": {
        # NCES College Navigator student-faculty ratio.
        "student_faculty_ratio": "11:1",
        # Georgetown Endowment Annual Letter FY2024 ($3.6B, fiscal year ended June 30, 2024).
        "endowment_usd": 3600000000,
    },
    "research": {
        "labs": [
            "O'Neill Institute for National and Global Health Law",
            "Lombardi Comprehensive Cancer Center",
            "Walsh School of Foreign Service centers and institutes",
            "Berkley Center for Religion, Peace, and World Affairs",
            "Massive Data Institute (McCourt School)",
            "Baker Center for Leadership & Governance",
            "Beeck Center for Social Impact + Innovation",
            "Georgetown Institute of Politics and Public Service",
        ],
        "areas": [
            "International affairs, diplomacy & security",
            "Health law, policy & biomedical research",
            "Public policy & governance",
            "Law",
            "Religion, peace & world affairs",
            "Cancer biology & oncology",
            "Data science for public policy",
        ],
        "lab_links": {
            "O'Neill Institute for National and Global Health Law": "https://oneill.law.georgetown.edu/",
            "Lombardi Comprehensive Cancer Center": "https://lombardi.georgetown.edu/",
            "Berkley Center for Religion, Peace, and World Affairs": "https://berkleycenter.georgetown.edu/",
            "Massive Data Institute (McCourt School)": "https://mccourt.georgetown.edu/research/the-massive-data-institute/",
            "Baker Center for Leadership & Governance": "https://bakercenter.georgetown.edu/",
            "Beeck Center for Social Impact + Innovation": "https://beeckcenter.georgetown.edu/",
            "Georgetown Institute of Politics and Public Service": "https://politics.georgetown.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big East Conference)",
        "mascot": "Georgetown Hoyas (Jack the Bulldog)",
        "housing": (
            "Residential campus on the Hilltop above the Potomac in the "
            "Georgetown neighborhood"
        ),
        "resources": [
            {"label": "Georgetown Hoyas Athletics", "url": "https://guhoyas.com/"},
            {"label": "Georgetown University Library", "url": "https://library.georgetown.edu/"},
            {
                "label": "Cawley Career Education Center",
                "url": "https://careercenter.georgetown.edu/",
            },
            {
                "label": "Georgetown Institute of Politics and Public Service",
                "url": "https://politics.georgetown.edu/",
            },
            {
                "label": "Healy Hall (National Historic Landmark)",
                "url": "https://www.georgetown.edu/",
            },
        ],
    },
    "flagship": {
        # NCES College Navigator (IPEDS fall 2024): total enrollment across all levels.
        "enrollment_total": 20031,
        # Georgetown Key Facts / Common Data Set 2024-25 — first-year admissions cycle.
        "applicants": 26131,
        "admits": 3374,
        "enrolled": 1598,
        "admissions_cycle": "Class of 2028 (entering fall 2024; CDS 2024-25)",
        "founded_year": 1789,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Georgetown, UNITID 131496)",
            "url": "https://collegescorecard.ed.gov/school/?131496",
        },
        {
            "label": "NCES College Navigator — Georgetown University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=131496",
        },
        {
            "label": "Georgetown University Bulletin — Schools & Programs",
            "url": "https://bulletin.georgetown.edu/",
        },
        {
            "label": "Georgetown University — Fall 2025-Spring 2026 Undergraduate Tuition",
            "url": "https://www.georgetown.edu/news/announcing-fall-2025-spring-2026-undergraduate-tuition-rates/",
        },
        {
            "label": "U.S. News Best Colleges — Georgetown University (#24 National Universities)",
            "url": "https://www.usnews.com/best-colleges/georgetown-university-1445",
        },
        {
            "label": "Georgetown Key Facts (admissions, enrollment)",
            "url": "https://www.georgetown.edu/about/key-facts/",
        },
        {
            "label": (
                "Georgetown Office of Student Financial Aid — 2025-26 Undergraduate Cost of "
                "Attendance"
            ),
            "url": "https://finaid.georgetown.edu/2425_undergraduate_coa/",
        },
        {
            "label": "Georgetown Endowment Annual Letter FY2024 ($3.6B)",
            "url": "https://oads.georgetown.edu/",
        },
        {
            "label": "QS World University Rankings 2026 — Georgetown University",
            "url": "https://www.topuniversities.com/universities/georgetown-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 (Georgetown)",
            "url": "https://www.timeshighereducation.com/world-university-rankings/georgetown-university",
        },
    ],
}

# Undergraduate enrollment (the page labels this field "Undergraduates").
UNDERGRAD_COUNT = 7833

DESCRIPTION = (
    "Georgetown University is a private Jesuit research university in Washington, DC, "
    "founded in 1789 as the oldest Catholic institution of higher education in the "
    "United States. Anchored by its landmark Healy Hall on a hill above the Potomac "
    "River, it enrolls students across its undergraduate colleges and graduate and "
    "professional schools and is classified as an R1 very-high-research-activity "
    "university. It is especially renowned for its Walsh School of Foreign Service, "
    "with additional strengths in government, law, business, and health."
)

# ── Schools / colleges ─────────────────────────────────────────────────────
CAS = "Georgetown College of Arts & Sciences"
SFS = "Walsh School of Foreign Service"
MSB = "McDonough School of Business"
NUR = "School of Nursing"
HEA = "School of Health"
GSAS = "Graduate School of Arts & Sciences"
MCCOURT = "McCourt School of Public Policy"
SCS = "School of Continuing Studies"
LAW = "Georgetown University Law Center"
MED = "School of Medicine"

SCHOOLS: list[dict] = [
    {
        "name": CAS,
        "sort_order": 1,
        "description": (
            "Georgetown's oldest and largest academic unit, the College of Arts & Sciences offers "
            "the undergraduate liberal-arts curriculum across the humanities, social sciences, and "
            "natural sciences on the historic Hilltop campus."
        ),
    },
    {
        "name": SFS,
        "sort_order": 2,
        "description": (
            "Founded in 1919, the Walsh School of Foreign Service is one of the world's preeminent "
            "schools of international affairs, offering the Bachelor of Science in Foreign Service "
            "and a suite of graduate degrees through its regional and functional centers."
        ),
    },
    {
        "name": MSB,
        "sort_order": 3,
        "description": (
            "The McDonough School of Business educates undergraduate, MBA, and "
            "specialized-master's students in global, values-based management, leveraging its "
            "Washington, DC location for access to government, policy, and international business."
        ),
    },
    {
        "name": MCCOURT,
        "sort_order": 4,
        "description": (
            "The McCourt School of Public Policy trains analysts and leaders in evidence-based "
            "policy through quantitative, analysis-driven graduate programs on Georgetown's "
            "Capitol Campus near the institutions of government."
        ),
    },
    {
        "name": NUR,
        "sort_order": 5,
        "description": (
            "The School of Nursing prepares nurses and nurse scientists from the bachelor's "
            "through the doctoral level, combining clinical practice in Washington, DC with the "
            "Jesuit commitment to whole-person, values-grounded care."
        ),
    },
    {
        "name": HEA,
        "sort_order": 6,
        "description": (
            "The School of Health advances education and research in global health, health systems "
            "management, and health policy, preparing undergraduate and graduate students to lead "
            "and reform health-care systems."
        ),
    },
    {
        "name": MED,
        "sort_order": 7,
        "description": (
            "Founded in 1851, the School of Medicine educates physicians through its Journeys "
            "Curriculum and trains biomedical scientists through Biomedical Graduate Education, "
            "grounded in the Jesuit ideal of cura personalis."
        ),
    },
    {
        "name": LAW,
        "sort_order": 8,
        "description": (
            "The Georgetown University Law Center, founded in 1870, is one of the largest and most "
            "prominent law schools in the United States, offering the J.D. and an extensive "
            "graduate-law curriculum steps from the Capitol and federal courts."
        ),
    },
    {
        "name": GSAS,
        "sort_order": 9,
        "description": (
            "The Graduate School of Arts & Sciences administers Georgetown's academic master's and "
            "doctoral programs across the humanities, social sciences, and natural sciences, "
            "supporting research and scholarship throughout the university."
        ),
    },
    {
        "name": SCS,
        "sort_order": 10,
        "description": (
            "The School of Continuing Studies serves working professionals and adult learners "
            "through its Master of Professional Studies degrees, liberal-studies programs, and "
            "continuing-education offerings on the downtown Capitol Campus."
        ),
    },
]

_SCHOOL_WEBSITE: dict[str, str] = {
    CAS: "https://college.georgetown.edu/",
    SFS: "https://sfs.georgetown.edu/",
    MSB: "https://msb.georgetown.edu/",
    MCCOURT: "https://mccourt.georgetown.edu/",
    NUR: "https://nursing.georgetown.edu/",
    HEA: "https://health.georgetown.edu/",
    MED: "https://som.georgetown.edu/",
    LAW: "https://www.law.georgetown.edu/",
    GSAS: "https://grad.georgetown.edu/",
    SCS: "https://scs.georgetown.edu/",
}

_SCHOOL_FOUNDED: dict[str, int] = {
    CAS: 1789,
    SFS: 1919,
    MSB: 1957,
    MCCOURT: 2013,
    NUR: 1903,
    MED: 1851,
    LAW: 1870,
    GSAS: 1820,
}

_SCHOOL_RESEARCH_CENTERS: dict[str, list[str]] = {
    CAS: [
        "Kennedy Institute of Ethics",
        "Center for Contemporary Arab Studies",
        "Georgetown Environment Initiative",
    ],
    SFS: [
        "Institute for the Study of Diplomacy",
        "Center for Security Studies",
        "Center for Eurasian, Russian and East European Studies",
        "Mortara Center for International Studies",
    ],
    MSB: [
        "Georgetown Entrepreneurship Initiative",
        "Steers Center for Global Real Estate",
        "Psychology of the Marketplace and Social Impact Lab",
    ],
    MCCOURT: [
        "Massive Data Institute",
        "Center on Education and the Workforce",
        "Georgetown Center on Poverty and Inequality",
    ],
    NUR: ["Center for Innovation, Resilience, and Community Leadership in Education"],
    HEA: ["Department of Global Health", "Health Systems Administration program research"],
    MED: [
        "Lombardi Comprehensive Cancer Center",
        "Georgetown-Howard Universities Center for Clinical and Translational Science",
    ],
    LAW: [
        "O'Neill Institute for National and Global Health Law",
        "Institute for Technology Law & Policy",
        "Center on National Security",
    ],
    GSAS: ["Interdisciplinary doctoral and master's research across the arts and sciences"],
    SCS: ["Center for Applied Intelligence and Cybersecurity research"],
}

# Leadership is omitted on each school: deans rotate and a stale name is worse than an
# honest gap (omit-never-guess).
_ABOUT_DETAIL: dict[str, dict] = {}
_ABOUT_OMITTED: dict[str, list[str]] = {}
for _s in SCHOOLS:
    _nm = _s["name"]
    _ab: dict = {"faculty": "Full-time faculty teaching and conducting research within the school."}
    if _nm in _SCHOOL_FOUNDED:
        _ab["founded"] = _SCHOOL_FOUNDED[_nm]
    if _nm in _SCHOOL_RESEARCH_CENTERS:
        _ab["research_centers"] = _SCHOOL_RESEARCH_CENTERS[_nm]
    _ABOUT_DETAIL[_nm] = _ab
    _om = ["about_detail.leadership"]
    if _nm not in _SCHOOL_FOUNDED:
        _om.append("about_detail.founded")
    _ABOUT_OMITTED[_nm] = _om

# ── Feeds (content_sources) ────────────────────────────────────────────────
# Verified live this session: feed.georgetown.edu/feed/ returns valid RSS (10 items);
# events.georgetown.edu/live/ical/events (LiveWhale) returns 136 VEVENTs.
_NEWS_RSS = "https://feed.georgetown.edu/feed/"
_EVENTS_FEED = "https://events.georgetown.edu/live/ical/events"
_SOCIAL = {
    "instagram": "https://www.instagram.com/georgetownuniversity/",
    "linkedin": "https://www.linkedin.com/school/georgetown-university/",
    "x": "https://twitter.com/georgetown",
    "youtube": "https://www.youtube.com/georgetownuniversity",
    "facebook": "https://www.facebook.com/georgetownuniv",
}

_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://www.georgetown.edu/news/",
    "events_feed": {"url": _EVENTS_FEED, "type": "ical"},
    "social": _SOCIAL,
}

# Keywords that filter the shared university feed to each school's items.
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    CAS: ["College", "Arts & Sciences", "Georgetown College"],
    SFS: ["School of Foreign Service", "SFS", "Walsh"],
    MSB: ["McDonough", "business", "MBA"],
    MCCOURT: ["McCourt", "public policy"],
    NUR: ["School of Nursing", "nursing"],
    HEA: ["School of Health", "global health"],
    MED: ["School of Medicine", "medical", "biomedical"],
    LAW: ["Law Center", "law", "Georgetown Law"],
    GSAS: ["Graduate School", "graduate", "research"],
    SCS: ["Continuing Studies", "professional studies"],
}


def _school_content(name: str) -> dict:
    base = dict(_INSTITUTION_CONTENT)
    base["keywords"] = list(_SCHOOL_KEYWORDS.get(name, []))
    return base


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    kws = list(base.get("keywords", []))
    base["keywords"] = list(keywords) + kws
    return base


# ── The program catalog (generated; verified per-program) ──────────────────
CATALOG = [
    {
        "slug": "georgetown-economics-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Economics",
        "degree_type": "bachelors",
        "department": "Department of Economics",
        "cip": "45.06",
        "delivery_format": "on_campus",
        "keywords": ["economics"],
        "description": (
            "Georgetown's economics major builds from micro- and macroeconomic theory into "
            "intermediate theory, statistics, and econometrics, culminating in a senior thesis "
            "that models competing hypotheses and tests them quantitatively in a Washington policy "
            "setting."
        ),
        "who_its_for": (
            "Students who want rigorous quantitative training for careers in finance, policy, "
            "consulting, or graduate study in economics."
        ),
    },
    {
        "slug": "georgetown-government-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Government",
        "degree_type": "bachelors",
        "department": "Department of Government",
        "cip": "45.10",
        "delivery_format": "on_campus",
        "keywords": ["government"],
        "description": (
            "Government at Georgetown is organized into four subfields—American government, "
            "comparative government, international relations, and political theory—with a required "
            "political-theory course reflecting the university's Jesuit commitment to ethics, "
            "justice, and rights."
        ),
        "who_its_for": (
            "Aspiring policymakers, lawyers, diplomats, and analysts who want to study political "
            "institutions in the nation's capital."
        ),
    },
    {
        "slug": "georgetown-political-economy-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Political Economy",
        "degree_type": "bachelors",
        "department": "Department of Economics and Department of Government",
        "cip": "45.06",
        "delivery_format": "on_campus",
        "keywords": ["political economy"],
        "description": (
            "Jointly managed by Economics and Government, this major studies how political and "
            "economic forces shape production and exchange—globalization, trade, regulation, "
            "development, and income distribution—using formal modeling, econometrics, and "
            "comparative case studies."
        ),
        "who_its_for": (
            "Students drawn to problems that straddle markets and politics and do not fit neatly "
            "within one discipline."
        ),
    },
    {
        "slug": "georgetown-sociology-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Sociology",
        "degree_type": "bachelors",
        "department": "Department of Sociology",
        "cip": "45.11",
        "delivery_format": "on_campus",
        "keywords": ["sociology"],
        "description": (
            "Sociology majors study gender and sexuality, race and ethnicity, social inequality, "
            "social movements, crime and deviance, urban studies, and demography, completing a "
            "two-semester senior thesis grounded in a junior-year research-methods course."
        ),
        "who_its_for": (
            "Students interested in social structure and inequality who want hands-on training in "
            "original empirical research."
        ),
    },
    {
        "slug": "georgetown-anthropology-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Anthropology",
        "degree_type": "bachelors",
        "department": "Department of Anthropology",
        "cip": "45.02",
        "delivery_format": "on_campus",
        "keywords": ["anthropology"],
        "description": (
            "Anthropology at Georgetown uses a four-field approach across the social sciences, "
            "humanities, and biological sciences, emphasizing ethnographic fieldwork and discourse "
            "analysis to examine race, language, religion, kinship, power, gender, and "
            "institutions like medicine and law."
        ),
        "who_its_for": (
            "Students curious about human cultures and societies who want ethnographic and "
            "cross-cultural research skills."
        ),
    },
    {
        "slug": "georgetown-psychology-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Psychology",
        "degree_type": "bachelors",
        "department": "Department of Psychology",
        "cip": "42.01",
        "delivery_format": "on_campus",
        "keywords": ["psychology"],
        "description": (
            "Psychology majors engage developmental, social, cultural, clinical, cognitive, and "
            "biological approaches alongside historical and theoretical perspectives, with active "
            "undergraduate research in areas like infant media learning and the cultural study of "
            "emotion."
        ),
        "who_its_for": (
            "Students interested in mind and behavior, including pre-health and future "
            "research-psychologist tracks."
        ),
    },
    {
        "slug": "georgetown-history-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in History",
        "degree_type": "bachelors",
        "department": "Department of History",
        "cip": "54.01",
        "delivery_format": "on_campus",
        "keywords": ["history"],
        "description": (
            "History majors concentrate on at least one of seven world regions across Africa, "
            "Asia, Latin America, the Middle East, Europe, Russia, and the United States, then "
            "broaden comparatively through seminar-driven writing and a senior reflective "
            "portfolio."
        ),
        "who_its_for": (
            "Students who want deep regional expertise plus the analytical writing valued in law, "
            "journalism, and government."
        ),
    },
    {
        "slug": "georgetown-philosophy-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Philosophy",
        "degree_type": "bachelors",
        "department": "Department of Philosophy",
        "cip": "38.01",
        "delivery_format": "on_campus",
        "keywords": ["philosophy"],
        "description": (
            "Philosophy trains students in logic, ethics, and the cluster of language, "
            "epistemology, metaphysics, mind, and science alongside historical texts, framed by "
            "the university's Catholic commitment to reflecting on faith and human existence."
        ),
        "who_its_for": (
            "Students seeking rigorous training in argument and ethical reasoning across any "
            "career path."
        ),
    },
    {
        "slug": "georgetown-theology-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Theology and Religious Studies",
        "degree_type": "bachelors",
        "department": "Department of Theology and Religious Studies",
        "cip": "38.02",
        "delivery_format": "on_campus",
        "keywords": ["theology and religious studies"],
        "description": (
            "The major offers five concentrations—Christian Theology, Biblical Studies, Ethics, "
            "Religious Studies, and Religion, Politics, and the Common Good—pairing comparative "
            "critical study of religious traditions with attention to their social, historical, "
            "and political contexts."
        ),
        "who_its_for": (
            "Students drawn to religious thought, ethics, and the role of faith in public life on "
            "a Jesuit campus."
        ),
    },
    {
        "slug": "georgetown-english-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in English",
        "degree_type": "bachelors",
        "department": "Department of English",
        "cip": "23.01",
        "delivery_format": "on_campus",
        "keywords": ["english"],
        "description": (
            "English majors study literature across periods and in a global frame, choosing "
            "optional concentrations in Global Cultures, Media, Genre, or Creative and Public "
            "Writing, supported by the Lannan Program's visiting writers."
        ),
        "who_its_for": (
            "Students who love close reading and writing and want flexibility to specialize in "
            "media or creative work."
        ),
    },
    {
        "slug": "georgetown-linguistics-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Linguistics",
        "degree_type": "bachelors",
        "department": "Department of Linguistics",
        "cip": "16.01",
        "delivery_format": "on_campus",
        "keywords": ["linguistics"],
        "description": (
            "Linguistics majors study phonology, syntax, and language history alongside "
            "sociolinguistics, language acquisition, psycholinguistics, and computational "
            "applications of linguistic knowledge to language teaching and computer science."
        ),
        "who_its_for": (
            "Students fascinated by how language works, including those eyeing computational or "
            "sociolinguistic careers."
        ),
    },
    {
        "slug": "georgetown-classics-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Classics",
        "degree_type": "bachelors",
        "department": "Department of Classics",
        "cip": "16.12",
        "delivery_format": "on_campus",
        "keywords": ["classics"],
        "description": (
            "Classics offers concentrations in Classical Studies, Hellenic Studies, Greek, Latin, "
            "and combined Greek and Latin, studying ancient Mediterranean civilizations through "
            "original-language texts as well as evidence read in English."
        ),
        "who_its_for": (
            "Students drawn to the ancient world and classical languages, whether beginners or "
            "advanced."
        ),
    },
    {
        "slug": "georgetown-arabic-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Arabic",
        "degree_type": "bachelors",
        "department": "Department of Arabic and Islamic Studies",
        "cip": "16.11",
        "delivery_format": "on_campus",
        "keywords": ["arabic"],
        "description": (
            "Home to the oldest undergraduate Arabic program in the United States, the major "
            "builds Modern Standard Arabic proficiency alongside classical and contemporary "
            "literature, linguistics, and Islamic civilization, requiring study abroad and an "
            "oral-proficiency capstone."
        ),
        "who_its_for": (
            "Students aiming for fluency in Arabic and expertise in the Middle East and Islamic "
            "world."
        ),
    },
    {
        "slug": "georgetown-chinese-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Chinese",
        "degree_type": "bachelors",
        "department": "Department of East Asian Languages and Cultures",
        "cip": "16.03",
        "delivery_format": "on_campus",
        "keywords": ["chinese"],
        "description": (
            "The Chinese major combines spoken and written Mandarin with critical study of Chinese "
            "literature, film, art, and philosophy, including classical Chinese, and requires "
            "immersion abroad plus a research-based senior seminar conducted largely in Chinese."
        ),
        "who_its_for": (
            "Students seeking advanced Chinese proficiency and deep engagement with Chinese "
            "culture."
        ),
    },
    {
        "slug": "georgetown-japanese-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Japanese",
        "degree_type": "bachelors",
        "department": "Department of East Asian Languages and Cultures",
        "cip": "16.03",
        "delivery_format": "on_campus",
        "keywords": ["japanese"],
        "description": (
            "The Japanese major pairs four years of language study with cultural, literary, and "
            "linguistic coursework, requiring a semester in Japan at partner universities such as "
            "Keio, Sophia, Waseda, or Nanzan and a substantial senior thesis."
        ),
        "who_its_for": (
            "Students who want fluency in Japanese and grounding in Japanese culture and society."
        ),
    },
    {
        "slug": "georgetown-korean-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Korean",
        "degree_type": "bachelors",
        "department": "Department of East Asian Languages and Cultures",
        "cip": "16.03",
        "delivery_format": "on_campus",
        "keywords": ["korean"],
        "description": (
            "The Korean major provides training in spoken and written Korean alongside study of "
            "Korean literature, film, and popular culture, requiring an approved semester abroad "
            "in Korea and a senior seminar culminating in a substantial thesis."
        ),
        "who_its_for": (
            "Students drawn to Korean language and contemporary Korean culture and media."
        ),
    },
    {
        "slug": "georgetown-east-asian-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in East Asian Languages and Cultures",
        "degree_type": "bachelors",
        "department": "Department of East Asian Languages and Cultures",
        "cip": "16.03",
        "delivery_format": "on_campus",
        "keywords": ["east asian languages and cultures"],
        "description": (
            "This regional major lets students study languages and cultures across East Asia "
            "rather than a single nation, building third-year proficiency in one East Asian "
            "language while taking comparative cultural coursework and a research capstone."
        ),
        "who_its_for": (
            "Students with cross-regional interests in East Asia who want comparative rather than "
            "single-country focus."
        ),
    },
    {
        "slug": "georgetown-french-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in French and Francophone Studies",
        "degree_type": "bachelors",
        "department": "Department of French and Francophone Studies",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["french and francophone studies"],
        "description": (
            "Majors develop a critical appreciation of French and Francophone cultures and "
            "literatures, refining language skills across a wide range of content areas and "
            "normally studying at a French or Francophone university, with an optional senior "
            "honors thesis."
        ),
        "who_its_for": (
            "Students seeking advanced French and broad engagement with the French-speaking world."
        ),
    },
    {
        "slug": "georgetown-german-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in German",
        "degree_type": "bachelors",
        "department": "Department of German",
        "cip": "16.05",
        "delivery_format": "on_campus",
        "keywords": ["german"],
        "description": (
            "The German major spans language, culture, literature, and linguistics through "
            "advanced coursework and text-based cultural analysis, requiring a significant "
            "study-abroad experience and preparing students for academic, institutional, and "
            "professional contexts."
        ),
        "who_its_for": "Students who want German proficiency plus literary and cultural depth.",
    },
    {
        "slug": "georgetown-italian-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Italian",
        "degree_type": "bachelors",
        "department": "Department of Italian Studies",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["italian"],
        "description": (
            "The Italian major takes an integrative approach from medieval and Renaissance "
            "foundations to modern topics including cinema, fashion, and Dante's Divine Comedy, "
            "requiring a semester or year of study at an Italian university."
        ),
        "who_its_for": (
            "Students who want fluency in Italian and immersion in Italian literature and culture."
        ),
    },
    {
        "slug": "georgetown-spanish-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Spanish",
        "degree_type": "bachelors",
        "department": "Department of Spanish and Portuguese",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["spanish"],
        "description": (
            "The Spanish major combines advanced language study with literature, culture, and "
            "linguistics coursework on Spain and Spanish America, culminating in a senior "
            "capstone, with students generally required to study in Spain or Spanish America."
        ),
        "who_its_for": (
            "Students seeking advanced Spanish and expertise in Hispanic literatures and cultures."
        ),
    },
    {
        "slug": "georgetown-portuguese-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Portuguese",
        "degree_type": "bachelors",
        "department": "Department of Spanish and Portuguese",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["portuguese"],
        "description": (
            "The Portuguese major studies the literatures, cultures, and linguistics of the "
            "Lusophone world through advanced language, conversation, and upper-level electives, "
            "requiring study abroad in Brazil or Portugal and emphasizing writing as critical "
            "thinking."
        ),
        "who_its_for": (
            "Students drawn to Brazil, Portugal, and the broader Portuguese-speaking world."
        ),
    },
    {
        "slug": "georgetown-russian-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Russian",
        "degree_type": "bachelors",
        "department": "Department of Slavic Languages",
        "cip": "16.04",
        "delivery_format": "on_campus",
        "keywords": ["russian"],
        "description": (
            "The Russian major develops reading, conversation, and analytic writing in Russian "
            "alongside study of major periods in Russian cultural and literary history and "
            "contemporary society, with a senior oral-proficiency exit interview."
        ),
        "who_its_for": (
            "Students seeking Russian fluency and grounding in Russian literature, culture, and "
            "current affairs."
        ),
    },
    {
        "slug": "georgetown-studio-art-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Art",
        "degree_type": "bachelors",
        "department": "Department of Art and Art History",
        "cip": "50.07",
        "delivery_format": "on_campus",
        "keywords": ["art"],
        "description": (
            "The studio art major offers concentrations in printmaking and drawing, painting, "
            "sculpture, or photography, graphic design, and new media, requiring ten studio "
            "courses plus art history, a senior seminar, and a Senior Majors Exhibition."
        ),
        "who_its_for": (
            "Students pursuing serious studio practice across traditional and new media."
        ),
    },
    {
        "slug": "georgetown-art-history-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Art History",
        "degree_type": "bachelors",
        "department": "Department of Art and Art History",
        "cip": "50.07",
        "delivery_format": "on_campus",
        "keywords": ["art history"],
        "description": (
            "Art History majors study the history, theory, and interpretation of visual art and "
            "material culture across periods, drawing on Washington's museums and collections as a "
            "teaching resource within the Department of Art and Art History."
        ),
        "who_its_for": (
            "Students interested in the history and criticism of visual art, including museum and "
            "curatorial paths."
        ),
    },
    {
        "slug": "georgetown-theater-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Theater and Performance Studies",
        "degree_type": "bachelors",
        "department": "Department of Performing Arts",
        "cip": "50.05",
        "delivery_format": "on_campus",
        "keywords": ["theater and performance studies"],
        "description": (
            "This major integrates critical inquiry with hands-on practice in acting, playwriting, "
            "design, and directing, connecting performance to storytelling, social justice, arts "
            "management, and education through faculty-mentored productions and apprenticeships."
        ),
        "who_its_for": (
            "Students who want to combine theatrical making with scholarly study of performance."
        ),
    },
    {
        "slug": "georgetown-music-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in American Musical Cultures",
        "degree_type": "bachelors",
        "department": "Department of Performing Arts",
        "cip": "50.09",
        "delivery_format": "on_campus",
        "keywords": ["american musical cultures"],
        "description": (
            "American Musical Cultures studies music through historical investigation, media "
            "studies, ethnographic research, theory and analysis, and performance, letting "
            "students build personalized paths across recording, composition, and cultural "
            "analysis of multiple genres."
        ),
        "who_its_for": (
            "Students interested in music as both creative practice and cultural study across "
            "American traditions."
        ),
    },
    {
        "slug": "georgetown-american-studies-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in American Studies",
        "degree_type": "bachelors",
        "department": "American Studies Program",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["american studies"],
        "description": (
            "This interdisciplinary major asks critical questions about power, identity, history, "
            "and American culture—reading artifacts from art and pop culture to protests and "
            "campaigns—drawing on history, English, art, music, sociology, government, and "
            "philosophy."
        ),
        "who_its_for": (
            "Students who want an interdisciplinary lens on American culture and society, "
            "culminating in a senior thesis."
        ),
    },
    {
        "slug": "georgetown-black-studies-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Black Studies",
        "degree_type": "bachelors",
        "department": "Department of Black Studies",
        "cip": "05.02",
        "delivery_format": "on_campus",
        "keywords": ["black studies"],
        "description": (
            "Black Studies examines Black culture, history, and experience in the United States, "
            "Africa, and the Black Atlantic diaspora, offering concentrations in Global Race and "
            "Ethnicity; Race, Space and Public Policy; and Creativity, Design and Emerging Forms."
        ),
        "who_its_for": (
            "Students engaged with the intellectual, political, and cultural life of Black "
            "communities worldwide."
        ),
    },
    {
        "slug": "georgetown-womens-gender-studies-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Women's and Gender Studies",
        "degree_type": "bachelors",
        "department": "Women's and Gender Studies Program",
        "cip": "05.02",
        "delivery_format": "on_campus",
        "keywords": ["women's and gender studies"],
        "description": (
            "This interdisciplinary, cross-cultural major explores women's rights, sexuality, and "
            "gender justice in global context, distributing across sexuality studies, cultural and "
            "media representations of gender, and race and racism, plus optional thematic "
            "concentrations."
        ),
        "who_its_for": (
            "Students applying feminist theory and methods to questions of gender, sexuality, and "
            "justice."
        ),
    },
    {
        "slug": "georgetown-justice-peace-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Justice and Peace Studies",
        "degree_type": "bachelors",
        "department": "Justice and Peace Studies Program",
        "cip": "30.05",
        "delivery_format": "on_campus",
        "keywords": ["justice and peace studies"],
        "description": (
            "This interdisciplinary major addresses how to realize peace and justice in practice, "
            "with core courses in nonviolence, peacebuilding and conflict transformation, and "
            "research methods, plus a service-action component and writing-intensive coursework."
        ),
        "who_its_for": (
            "Students committed to social justice, conflict resolution, and human-rights work."
        ),
    },
    {
        "slug": "georgetown-medieval-studies-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Global Medieval Studies",
        "degree_type": "bachelors",
        "department": "Global Medieval Studies Program",
        "cip": "30.13",
        "delivery_format": "on_campus",
        "keywords": ["global medieval studies"],
        "description": (
            "This interdisciplinary major studies the medieval world across art, music, "
            "philosophy, literature, history, and theology from China to the Middle East to "
            "Europe, with distribution requirements ensuring coverage both within and beyond "
            "Europe."
        ),
        "who_its_for": (
            "Students drawn to the global Middle Ages across multiple disciplines and regions."
        ),
    },
    {
        "slug": "georgetown-comparative-literature-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Global and Comparative Literature",
        "degree_type": "bachelors",
        "department": "Global and Comparative Literature Program",
        "cip": "16.01",
        "delivery_format": "on_campus",
        "keywords": ["global and comparative literature"],
        "description": (
            "Majors study literatures and media within their cultural contexts across two "
            "traditions, reading works in their original languages and drawing connections to "
            "philosophy, politics, the arts, or film, with concentrations from nine language "
            "departments."
        ),
        "who_its_for": (
            "Multilingual students who want to study literature comparatively across cultures and "
            "languages."
        ),
    },
    {
        "slug": "georgetown-public-policy-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Public Policy",
        "degree_type": "bachelors",
        "department": "Joint Program with the McCourt School of Public Policy",
        "cip": "44.05",
        "delivery_format": "on_campus",
        "keywords": ["public policy"],
        "description": (
            "Offered jointly with the McCourt School, this major pairs liberal-arts education on "
            "the Hilltop with policy analysis and evaluation skills on the Capitol Campus, "
            "requiring methods electives and either a policy internship seminar or a hands-on "
            "policy lab."
        ),
        "who_its_for": (
            "Students aiming for careers in policy analysis, government, and public affairs in "
            "Washington."
        ),
    },
    {
        "slug": "georgetown-cs-ethics-society-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Computer Science, Ethics, and Society",
        "degree_type": "bachelors",
        "department": "Department of Computer Science",
        "cip": "11.07",
        "delivery_format": "on_campus",
        "keywords": ["computer science, ethics, and society"],
        "description": (
            "This major combines technical computer-science training with study of digital ethics, "
            "law, and policy, swapping calculus for probability and statistics and adding courses "
            "in tech ethics, digital law and policy, and a project-based senior capstone."
        ),
        "who_its_for": (
            "Students interested in technology law, tech policy, or the ethical stakes of "
            "computing."
        ),
    },
    {
        "slug": "georgetown-computer-science-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Computer Science",
        "degree_type": "bachelors",
        "department": "Department of Computer Science",
        "cip": "11.07",
        "delivery_format": "on_campus",
        "keywords": ["computer science"],
        "description": (
            "The A.B. in Computer Science offers broad, flexible requirements ideal for combining "
            "computing with another field such as mathematics, biology, government, linguistics, "
            "or philosophy, while covering core programming, theory, and systems."
        ),
        "who_its_for": (
            "Students who want to pair computer science with a second discipline rather than a "
            "purely technical path."
        ),
    },
    {
        "slug": "georgetown-computer-science-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Computer Science",
        "degree_type": "bachelors",
        "department": "Department of Computer Science",
        "cip": "11.07",
        "delivery_format": "on_campus",
        "keywords": ["computer science"],
        "description": (
            "The B.S. is the department's most technical undergraduate offering, with greater "
            "depth in programming, algorithms, theory, and systems to prepare students for "
            "industry careers or graduate study in computer science."
        ),
        "who_its_for": (
            "Students headed for technical software careers or graduate study in computing."
        ),
    },
    {
        "slug": "georgetown-mathematics-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Mathematics",
        "degree_type": "bachelors",
        "department": "Department of Mathematics and Statistics",
        "cip": "27.01",
        "delivery_format": "on_campus",
        "keywords": ["mathematics"],
        "description": (
            "The A.B. in Mathematics covers calculus, linear algebra, differential equations, "
            "proof-writing, abstract algebra, and analysis with upper-level electives, designed "
            "for students applying mathematics in fields like medicine, law, business, or "
            "teaching."
        ),
        "who_its_for": (
            "Students who want a strong mathematical foundation alongside another career or major."
        ),
    },
    {
        "slug": "georgetown-mathematics-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Mathematics",
        "degree_type": "bachelors",
        "department": "Department of Mathematics and Statistics",
        "cip": "27.01",
        "delivery_format": "on_campus",
        "keywords": ["mathematics"],
        "description": (
            "The more rigorous B.S. adds statistics, complex analysis, and programming "
            "requirements, preparing students for graduate study or quantitative employment, with "
            "the option to count a math-intensive course in another discipline."
        ),
        "who_its_for": (
            "Students aiming for graduate study or quantitative careers grounded in advanced "
            "mathematics."
        ),
    },
    {
        "slug": "georgetown-biology-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Biology",
        "degree_type": "bachelors",
        "department": "Department of Biology",
        "cip": "26.01",
        "delivery_format": "on_campus",
        "keywords": ["biology"],
        "description": (
            "Biology gives a comprehensive view of ecology, evolutionary biology, molecular and "
            "cell biology, and development, with concentrations in either Ecology, Evolution, and "
            "Behavioral Biology or Biochemistry, Molecular, Cellular, and Developmental Biology."
        ),
        "who_its_for": (
            "Students pursuing research, medicine, or graduate study across the biological "
            "sciences."
        ),
    },
    {
        "slug": "georgetown-environmental-biology-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Environmental Biology",
        "degree_type": "bachelors",
        "department": "Department of Biology",
        "cip": "26.13",
        "delivery_format": "on_campus",
        "keywords": ["environmental biology"],
        "description": (
            "Environmental Biology studies the biological, chemical, and geological processes "
            "operating on the planet and how human cultural, economic, agricultural, and "
            "public-health activity modifies environmental systems."
        ),
        "who_its_for": (
            "Students focused on ecology, conservation, and human-environment interactions."
        ),
    },
    {
        "slug": "georgetown-biology-global-health-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Biology of Global Health",
        "degree_type": "bachelors",
        "department": "Department of Biology",
        "cip": "26.01",
        "delivery_format": "on_campus",
        "keywords": ["biology of global health"],
        "description": (
            "This major examines the biology behind global health concerns, emphasizing infectious "
            "and genetic disease, through laboratory and quantitative science while integrating "
            "perspectives from policy, economics, ethics, and culture."
        ),
        "who_its_for": (
            "Pre-health and global-health students who want biological rigor paired with policy "
            "and ethics."
        ),
    },
    {
        "slug": "georgetown-neurobiology-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Neurobiology",
        "degree_type": "bachelors",
        "department": "Department of Biology",
        "cip": "26.15",
        "delivery_format": "on_campus",
        "keywords": ["neurobiology"],
        "description": (
            "Neurobiology focuses on the molecules, cells, and circuits that produce brain "
            "function, examining the nervous system from molecular and cellular mechanisms through "
            "developmental and cognitive dimensions."
        ),
        "who_its_for": (
            "Students drawn to the biology of the brain and nervous system, including pre-health "
            "paths."
        ),
    },
    {
        "slug": "georgetown-chemistry-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Chemistry",
        "degree_type": "bachelors",
        "department": "Department of Chemistry",
        "cip": "40.05",
        "delivery_format": "on_campus",
        "keywords": ["chemistry"],
        "description": (
            "The American Chemical Society-certified Chemistry major spans organic, physical, "
            "analytical, inorganic, and biochemistry, with strong emphasis on undergraduate "
            "research through programs like GUROP and an honors thesis track."
        ),
        "who_its_for": (
            "Students headed for chemistry graduate study, research, industry, or medical and "
            "professional school."
        ),
    },
    {
        "slug": "georgetown-biochemistry-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Biochemistry",
        "degree_type": "bachelors",
        "department": "Department of Chemistry",
        "cip": "26.02",
        "delivery_format": "on_campus",
        "keywords": ["biochemistry"],
        "description": (
            "The Biochemistry major provides rigorous training through specialized lecture and lab "
            "courses at the chemistry-biology interface and is especially well suited to students "
            "aspiring to MD-PhD programs or graduate study in biochemistry."
        ),
        "who_its_for": (
            "Students at the chemistry-biology interface, particularly MD-PhD and research "
            "aspirants."
        ),
    },
    {
        "slug": "georgetown-physics-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Physics",
        "degree_type": "bachelors",
        "department": "Department of Physics",
        "cip": "40.08",
        "delivery_format": "on_campus",
        "keywords": ["physics"],
        "description": (
            "The Physics B.S. builds from introductory courses into advanced study for students "
            "pursuing graduate work or careers in physics, science, or technology, with a "
            "research-oriented sequence in mechanics, electromagnetism, and quantum theory."
        ),
        "who_its_for": (
            "Students preparing for graduate study or technical careers in physics and related "
            "sciences."
        ),
    },
    {
        "slug": "georgetown-physics-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Physics",
        "degree_type": "bachelors",
        "department": "Department of Physics",
        "cip": "40.08",
        "delivery_format": "on_campus",
        "keywords": ["physics"],
        "description": (
            "The A.B. in Physics requires fewer advanced courses than the B.S., giving students "
            "greater flexibility to pursue a second major or careers outside science such as "
            "medicine, law, business, or teaching."
        ),
        "who_its_for": (
            "Students who want a physics foundation alongside another major or non-research career."
        ),
    },
    {
        "slug": "georgetown-biological-physics-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Biological Physics",
        "degree_type": "bachelors",
        "department": "Department of Physics",
        "cip": "40.08",
        "delivery_format": "on_campus",
        "keywords": ["biological physics"],
        "description": (
            "Biological Physics prepares students for graduate study or careers in biophysical, "
            "biomedical, or bioengineering fields, combining advanced physics with corollary "
            "biology and chemistry coursework."
        ),
        "who_its_for": (
            "Students at the physics-biology interface heading toward biophysics, biomedicine, or "
            "bioengineering."
        ),
    },
    {
        "slug": "georgetown-environment-sustainability-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in Environment and Sustainability",
        "degree_type": "bachelors",
        "department": "Environment and Sustainability Program (with the Earth Commons Institute)",
        "cip": "03.01",
        "delivery_format": "on_campus",
        "keywords": ["environment and sustainability"],
        "description": (
            "Offered with the Earth Commons Institute, this major moves students from the Hilltop "
            "to the Capitol Campus, combining environmental and sustainability science with custom "
            "upper-division pathways, a professional internship, and a year-long capstone "
            "symposium."
        ),
        "who_its_for": (
            "Students who want hands-on, interdisciplinary training to become environmental "
            "changemakers in DC and beyond."
        ),
    },
    {
        "slug": "georgetown-international-business-language-culture-bs",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Science in International Business, Language, and Culture",
        "degree_type": "bachelors",
        "department": (
            "International Business, Language and Culture Program (with the McDonough School of "
            "Business)"
        ),
        "cip": "52.11",
        "delivery_format": "on_campus",
        "keywords": ["international business, language, and culture"],
        "description": (
            "This joint College and McDonough major integrates an international business core with "
            "a chosen language concentration from ten languages, treating cultural and linguistic "
            "competency as central to the global business sector."
        ),
        "who_its_for": (
            "Students who want to combine business training with deep language and cultural "
            "expertise for global careers."
        ),
    },
    {
        "slug": "georgetown-interdisciplinary-studies-ab",
        "school": "Georgetown College of Arts & Sciences",
        "program_name": "Bachelor of Arts in Interdisciplinary Studies",
        "degree_type": "bachelors",
        "department": "Georgetown College Interdisciplinary Studies",
        "cip": "30.99",
        "delivery_format": "on_campus",
        "keywords": ["interdisciplinary studies"],
        "description": (
            "This self-designed major lets students integrate methods from two or more College "
            "disciplines to pursue a complex research question, working with two faculty advisors "
            "and a dean across four semesters toward a senior thesis or creative project."
        ),
        "who_its_for": (
            "Self-directed students whose intellectual question spans more than one existing major."
        ),
    },
    {
        "slug": "georgetown-international-politics-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": "Bachelor of Science in Foreign Service in International Politics",
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["international politics"],
        "description": (
            "This BSFS major examines global political dynamics, foreign-policy decision-making, "
            "international security, and the behavior of states and institutions, building "
            "analytical skills for understanding contemporary geopolitical conflict and "
            "cooperation."
        ),
        "who_its_for": (
            "An undergraduate aiming for diplomacy, foreign policy, or international-security "
            "careers who wants rigorous training in how states and global institutions interact."
        ),
    },
    {
        "slug": "georgetown-international-economics-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": "Bachelor of Science in Foreign Service in International Economics",
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "45.06",
        "delivery_format": "on_campus",
        "keywords": ["international economics"],
        "description": (
            "This BSFS major develops advanced micro- and macroeconomic analysis applied to trade, "
            "finance, and development, equipping students to interpret global markets and "
            "international economic policy."
        ),
        "who_its_for": (
            "A quantitatively inclined undergraduate headed toward international economic policy, "
            "trade, or finance work."
        ),
    },
    {
        "slug": "georgetown-international-political-economy-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": "Bachelor of Science in Foreign Service in International Political Economy",
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["international political economy"],
        "description": (
            "This BSFS major studies the intersection of economics and politics in the global "
            "system, culminating in senior thesis research on how markets, states, and "
            "institutions shape one another across borders."
        ),
        "who_its_for": (
            "An undergraduate drawn to the politics-economics nexus who wants to produce original "
            "research on global governance."
        ),
    },
    {
        "slug": "georgetown-culture-politics-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": "Bachelor of Science in Foreign Service in Culture and Politics",
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["culture and politics"],
        "description": (
            "This BSFS major explores the relationship between culture, knowledge, and power, "
            "drawing on social theory and the humanities to interrogate how identity, ideology, "
            "and representation shape world politics."
        ),
        "who_its_for": (
            "An interdisciplinary undergraduate interested in the cultural and theoretical "
            "dimensions of global affairs."
        ),
    },
    {
        "slug": "georgetown-regional-comparative-studies-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": (
            "Bachelor of Science in Foreign Service in Regional and Comparative Studies"
        ),
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["regional and comparative studies"],
        "description": (
            "This BSFS major builds deep expertise in two world regions through intensive language "
            "study and comparative coursework in their history, politics, and culture to address "
            "region-specific global challenges."
        ),
        "who_its_for": (
            "An undergraduate who wants language fluency and concentrated mastery of more than one "
            "part of the world."
        ),
    },
    {
        "slug": "georgetown-global-business-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": "Bachelor of Science in Foreign Service in Global Business",
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "52.11",
        "delivery_format": "on_campus",
        "keywords": ["global business"],
        "description": (
            "This BSFS major combines core business principles with perspectives on politics and "
            "culture to prepare students for careers spanning the private, public, and nonprofit "
            "sectors in an interconnected global economy."
        ),
        "who_its_for": (
            "An undergraduate who wants business fundamentals grounded in international political "
            "and cultural context."
        ),
    },
    {
        "slug": "georgetown-stia-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": (
            "Bachelor of Science in Foreign Service in Science, Technology and International "
            "Affairs"
        ),
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "30.15",
        "delivery_format": "on_campus",
        "keywords": ["science, technology and international affairs"],
        "description": (
            "This BSFS major merges science and technology interests with policy analysis on "
            "global issues such as climate, health, cybersecurity, and energy, bridging the "
            "technical and diplomatic worlds."
        ),
        "who_its_for": (
            "A science- or tech-minded undergraduate who wants to shape policy on technological "
            "and environmental challenges."
        ),
    },
    {
        "slug": "georgetown-international-history-bsfs",
        "school": "Walsh School of Foreign Service",
        "program_name": "Bachelor of Science in Foreign Service in International History",
        "degree_type": "bachelors",
        "department": "Walsh School of Foreign Service",
        "cip": "54.01",
        "delivery_format": "on_campus",
        "keywords": ["international history"],
        "description": (
            "This BSFS major examines global historical transformations across centuries and "
            "regions to build the critical and contextual thinking needed to interpret "
            "contemporary international issues."
        ),
        "who_its_for": (
            "An undergraduate who wants historical depth as the foundation for understanding "
            "today's world affairs."
        ),
    },
    {
        "slug": "georgetown-foreign-service-ms",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Science in Foreign Service",
        "degree_type": "masters",
        "department": "Walsh School of Foreign Service",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["foreign service"],
        "description": (
            "MSFS bridges international relations, economics, and history in a 48-credit "
            "professional curriculum with concentrations in global politics and security, "
            "international development, global business and finance, or science and technology."
        ),
        "who_its_for": (
            "An early-career professional preparing for leadership in government, international "
            "organizations, business, or civil society."
        ),
    },
    {
        "slug": "georgetown-security-studies-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in Security Studies",
        "degree_type": "masters",
        "department": "Center for Security Studies",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["security studies"],
        "description": (
            "The Security Studies Program trains analysts and policymakers through a "
            "multidisciplinary 36-credit curriculum spanning the military, technological, "
            "economic, and regional dimensions of national and international security."
        ),
        "who_its_for": (
            "A professional or recent graduate pursuing a career in defense, intelligence, or "
            "security policy."
        ),
    },
    {
        "slug": "georgetown-global-human-development-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Global Human Development",
        "degree_type": "masters",
        "department": "Global Human Development Program",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["master of global human development"],
        "description": (
            "This program prepares practitioners for sustainable, human-centered international "
            "development through training in poverty alleviation, monitoring and evaluation, "
            "social innovation, and inclusive growth across multilateral, nonprofit, and private "
            "settings."
        ),
        "who_its_for": (
            "An aspiring development professional headed for consulting, multilateral "
            "institutions, or global-policy work."
        ),
    },
    {
        "slug": "georgetown-arab-studies-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in Arab Studies",
        "degree_type": "masters",
        "department": "Center for Contemporary Arab Studies",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["arab studies"],
        "description": (
            "The Center for Contemporary Arab Studies trains students in the contemporary Arab "
            "world's language, history, society, politics, and economics through interdisciplinary "
            "coursework and intensive language instruction on the MENA region."
        ),
        "who_its_for": (
            "A student seeking regional and language mastery for careers focused on the Middle "
            "East and North Africa."
        ),
    },
    {
        "slug": "georgetown-asian-studies-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in Asian Studies",
        "degree_type": "masters",
        "department": "Asian Studies Program",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["asian studies"],
        "description": (
            "This program combines deep regional knowledge of a globalizing Asia with functional "
            "concentrations in security and politics, political economy, history and culture, or "
            "environment, energy, and transnational issues."
        ),
        "who_its_for": (
            "A student building Asia expertise for government, business, or scholarly careers."
        ),
    },
    {
        "slug": "georgetown-ceres-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in Eurasian, Russian and East European Studies",
        "degree_type": "masters",
        "department": "Center for Eurasian, Russian and East European Studies",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["eurasian, russian and east european studies"],
        "description": (
            "CERES builds broad command of the politics, history, economics, language, and culture "
            "of a region stretching from Central Europe to the Pacific, anchored by advanced "
            "regional-language study."
        ),
        "who_its_for": (
            "A student with strong regional-language skills targeting policy, security, or "
            "research roles on the post-Soviet space and Eastern Europe."
        ),
    },
    {
        "slug": "georgetown-european-studies-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in European Studies",
        "degree_type": "masters",
        "department": "BMW Center for German and European Studies",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["european studies"],
        "description": (
            "The BMW Center provides broad knowledge of European affairs grounded in comparative "
            "politics, cultural studies, economics, history, and international relations, with "
            "partnership exchanges such as the Hertie School in Berlin."
        ),
        "who_its_for": (
            "A student with European-language proficiency pursuing transatlantic policy, research, "
            "or diplomacy careers."
        ),
    },
    {
        "slug": "georgetown-latin-american-studies-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in Latin American Studies",
        "degree_type": "masters",
        "department": "Center for Latin American Studies",
        "cip": "05.01",
        "delivery_format": "on_campus",
        "keywords": ["latin american studies"],
        "description": (
            "This 36-credit program fosters cross-disciplinary study of Latin America and the "
            "Caribbean across politics, economics, history, and culture, training the hemisphere's "
            "next generation of leaders and scholars."
        ),
        "who_its_for": (
            "A student focused on Latin America and the Caribbean for policy, development, or "
            "academic careers."
        ),
    },
    {
        "slug": "georgetown-migration-refugees-ma",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Arts in International Migration and Refugees",
        "degree_type": "masters",
        "department": "Institute for the Study of International Migration",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["international migration and refugees"],
        "description": (
            "This program addresses the policy challenges of population movement and displacement, "
            "preparing professionals to navigate the intersections of migration, humanitarian "
            "response, and law and policymaking worldwide."
        ),
        "who_its_for": (
            "A professional or graduate pursuing migration, refugee, and humanitarian policy work."
        ),
    },
    {
        "slug": "georgetown-environment-international-affairs-ms",
        "school": "Walsh School of Foreign Service",
        "program_name": "Master of Science in Environment and International Affairs",
        "degree_type": "masters",
        "department": "Science, Technology and International Affairs Program",
        "cip": "45.09",
        "delivery_format": "on_campus",
        "keywords": ["environment and international affairs"],
        "description": (
            "Offered with the Earth Commons Institute, this program joins interdisciplinary "
            "environmental science with international policy to train experts who can confront "
            "pressing global environmental and sustainability challenges."
        ),
        "who_its_for": (
            "A student bridging environmental science and policy for climate, energy, and "
            "sustainability careers."
        ),
    },
    {
        "slug": "georgetown-bsba-accounting",
        "school": "McDonough School of Business",
        "program_name": "Bachelor of Science in Business Administration in Accounting",
        "degree_type": "bachelors",
        "department": "McDonough School of Business",
        "cip": "52.03",
        "delivery_format": "on_campus",
        "keywords": ["accounting"],
        "description": (
            "This major trains students in financial and managerial accounting, auditing, "
            "taxation, and the analysis of corporate financial statements, preparing them to read "
            "and construct the records that drive business decisions and capital markets."
        ),
        "who_its_for": (
            "Undergraduates aiming for careers in public accounting, corporate finance, or "
            "CPA-track professional roles."
        ),
    },
    {
        "slug": "georgetown-bsba-finance",
        "school": "McDonough School of Business",
        "program_name": "Bachelor of Science in Business Administration in Finance",
        "degree_type": "bachelors",
        "department": "McDonough School of Business",
        "cip": "52.08",
        "delivery_format": "on_campus",
        "keywords": ["finance"],
        "description": (
            "This major covers corporate finance, investments, capital markets, and valuation, "
            "teaching students to allocate capital, price risk, and analyze how firms and "
            "investors raise and deploy money in global markets."
        ),
        "who_its_for": (
            "Undergraduates targeting investment banking, asset management, corporate finance, or "
            "private equity."
        ),
    },
    {
        "slug": "georgetown-bsba-international-business",
        "school": "McDonough School of Business",
        "program_name": "Bachelor of Science in Business Administration in International Business",
        "degree_type": "bachelors",
        "department": "McDonough School of Business",
        "cip": "52.11",
        "delivery_format": "on_campus",
        "keywords": ["international business"],
        "description": (
            "This major examines how firms operate across borders, including global trade, "
            "cross-cultural management, foreign markets, and the political and economic forces "
            "shaping multinational strategy, leveraging Georgetown's location and global focus."
        ),
        "who_its_for": (
            "Undergraduates drawn to multinational companies, global strategy, or international "
            "development roles."
        ),
    },
    {
        "slug": "georgetown-bsba-management",
        "school": "McDonough School of Business",
        "program_name": "Bachelor of Science in Business Administration in Management",
        "degree_type": "bachelors",
        "department": "McDonough School of Business",
        "cip": "52.02",
        "delivery_format": "on_campus",
        "keywords": ["management"],
        "description": (
            "This major focuses on organizational behavior, leadership, strategy, and human "
            "capital, teaching students to design organizations, lead teams, and make strategic "
            "decisions that align people and resources with business goals."
        ),
        "who_its_for": (
            "Undergraduates pursuing leadership, consulting, entrepreneurship, or "
            "general-management career tracks."
        ),
    },
    {
        "slug": "georgetown-bsba-marketing",
        "school": "McDonough School of Business",
        "program_name": "Bachelor of Science in Business Administration in Marketing",
        "degree_type": "bachelors",
        "department": "McDonough School of Business",
        "cip": "52.14",
        "delivery_format": "on_campus",
        "keywords": ["marketing"],
        "description": (
            "This major studies consumer behavior, brand strategy, market research, pricing, and "
            "digital and analytical marketing, teaching students how firms identify customer needs "
            "and design products, messaging, and channels to meet them."
        ),
        "who_its_for": (
            "Undergraduates aiming for brand management, advertising, market research, or product "
            "marketing."
        ),
    },
    {
        "slug": "georgetown-bsba-operations-analytics",
        "school": "McDonough School of Business",
        "program_name": (
            "Bachelor of Science in Business Administration in Operations and Analytics"
        ),
        "degree_type": "bachelors",
        "department": "McDonough School of Business",
        "cip": "52.13",
        "delivery_format": "on_campus",
        "keywords": ["operations and analytics"],
        "description": (
            "This major combines operations management, supply chain, and data analytics, teaching "
            "students to use quantitative models and information systems to optimize processes, "
            "manage logistics, and turn data into operational decisions."
        ),
        "who_its_for": (
            "Undergraduates interested in supply chain, business analytics, consulting, or "
            "operations roles."
        ),
    },
    {
        "slug": "georgetown-mba-fulltime",
        "school": "McDonough School of Business",
        "program_name": "Master of Business Administration (Full-time)",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.02",
        "delivery_format": "on_campus",
        "keywords": ["master of business administration (full-time)"],
        "description": (
            "A two-year general-management MBA built on a values-based core, featuring the "
            "signature Global Business Experience consulting project and certificates in areas "
            "such as sustainability, consumer analytics, and healthcare."
        ),
        "who_its_for": (
            "Early- and mid-career professionals seeking a full-time, immersive MBA and a career "
            "pivot or acceleration."
        ),
    },
    {
        "slug": "georgetown-mba-flex",
        "school": "McDonough School of Business",
        "program_name": "Master of Business Administration (Flex)",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.02",
        "delivery_format": "hybrid",
        "keywords": ["master of business administration (flex)"],
        "description": (
            "The part-time Flex MBA delivers the same management curriculum on a flexible "
            "schedule, letting working professionals study in person or online while continuing to "
            "work full time."
        ),
        "who_its_for": (
            "Working professionals who want a Georgetown MBA without pausing their careers."
        ),
    },
    {
        "slug": "georgetown-finance-ms",
        "school": "McDonough School of Business",
        "program_name": "Master of Science in Finance",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.08",
        "delivery_format": "hybrid",
        "keywords": ["finance"],
        "description": (
            "A part-time, finance-focused master's covering valuation, financial modeling, "
            "investments, and risk, designed for working professionals who want advanced "
            "quantitative finance training while staying employed."
        ),
        "who_its_for": (
            "Finance professionals seeking deep quantitative and technical finance expertise."
        ),
    },
    {
        "slug": "georgetown-business-analytics-ms",
        "school": "McDonough School of Business",
        "program_name": "Master of Science in Business Analytics",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.13",
        "delivery_format": "on_campus",
        "keywords": ["business analytics"],
        "description": (
            "A STEM-designated program teaching data modeling, machine learning, and analytics "
            "tools applied to real business problems, offered in a 10-month full-time or 16-month "
            "online part-time format."
        ),
        "who_its_for": (
            "Professionals and recent graduates aiming for data-driven analytics and "
            "decision-science roles."
        ),
    },
    {
        "slug": "georgetown-management-ms",
        "school": "McDonough School of Business",
        "program_name": "Master of Science in Management",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.02",
        "delivery_format": "on_campus",
        "keywords": ["management"],
        "description": (
            "A 10-month, STEM-designated pre-experience master's that gives recent graduates "
            "business fundamentals, data analytics, and technology skills to launch careers in "
            "management, consulting, or analytics."
        ),
        "who_its_for": (
            "Recent non-business graduates seeking foundational management training before their "
            "first role."
        ),
    },
    {
        "slug": "georgetown-global-real-assets-ms",
        "school": "McDonough School of Business",
        "program_name": "Master of Science in Global Real Assets",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.15",
        "delivery_format": "on_campus",
        "keywords": ["global real assets"],
        "description": (
            "This program focuses on the investment and management of real estate, infrastructure, "
            "and other tangible assets, teaching students to evaluate, finance, and develop "
            "large-scale real-asset projects across global markets."
        ),
        "who_its_for": (
            "Professionals targeting real estate, infrastructure, and real-asset investment "
            "careers."
        ),
    },
    {
        "slug": "georgetown-environment-sustainability-management-ms",
        "school": "McDonough School of Business",
        "program_name": "Master of Science in Environment and Sustainability Management",
        "degree_type": "masters",
        "department": "McDonough School of Business",
        "cip": "52.02",
        "delivery_format": "on_campus",
        "keywords": ["environment and sustainability management"],
        "description": (
            "A joint degree from the Earth Commons, McDonough, and the Graduate School that blends "
            "environmental science with business principles to prepare leaders for sustainability "
            "strategy and management roles."
        ),
        "who_its_for": (
            "Professionals bridging environmental science and business in sustainability-focused "
            "careers."
        ),
    },
    {
        "slug": "georgetown-international-business-policy-ma",
        "school": "McDonough School of Business",
        "program_name": "Master of Arts in International Business and Policy",
        "degree_type": "masters",
        "department": "McDonough School of Business and Walsh School of Foreign Service",
        "cip": "52.11",
        "delivery_format": "hybrid",
        "keywords": ["international business and policy"],
        "description": (
            "A modular master's at the intersection of business and public policy, teaching senior "
            "professionals to navigate global markets, geopolitics, regulation, and the forces "
            "linking governments and multinational enterprise."
        ),
        "who_its_for": (
            "Experienced executives working at the crossroads of business, government, and global "
            "policy."
        ),
    },
    {
        "slug": "georgetown-nursing-bsn",
        "school": "School of Nursing",
        "program_name": "Bachelor of Science in Nursing",
        "degree_type": "bachelors",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "on_campus",
        "keywords": ["nursing"],
        "description": (
            "This program combines clinical rotations across Washington, DC hospitals with "
            "coursework in pathophysiology, pharmacology, and population health, training nurses "
            "through a Jesuit lens of whole-person, values-grounded care."
        ),
        "who_its_for": (
            "First-time college students who want to become registered nurses through a "
            "traditional four-year, campus-based pathway."
        ),
    },
    {
        "slug": "georgetown-nursing-entry-ms",
        "school": "School of Nursing",
        "program_name": "Master of Science Entry to Nursing",
        "degree_type": "masters",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "on_campus",
        "keywords": ["master of science entry to nursing"],
        "description": (
            "A five-semester, direct-entry program that takes graduates of non-nursing fields "
            "through accelerated nursing science and clinical practice to prepare them for "
            "licensure as registered nurses."
        ),
        "who_its_for": (
            "Career-changers who already hold a bachelor's degree in another field and want to "
            "enter nursing."
        ),
    },
    {
        "slug": "georgetown-nursing-ms",
        "school": "School of Nursing",
        "program_name": "Master of Science in Nursing",
        "degree_type": "masters",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "online",
        "keywords": ["nursing"],
        "description": (
            "This program prepares licensed RNs to become advanced-practice nurse practitioners "
            "through specialty tracks in family, adult-gerontology acute care, women's health, or "
            "nurse-midwifery, blending distance coursework with clinical intensives."
        ),
        "who_its_for": (
            "Registered nurses with a BSN seeking advanced-practice certification as a nurse "
            "practitioner."
        ),
    },
    {
        "slug": "georgetown-nurse-anesthesia-dnap",
        "school": "School of Nursing",
        "program_name": "Doctor of Nurse Anesthesia Practice",
        "degree_type": "professional",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "on_campus",
        "keywords": ["doctor of nurse anesthesia practice"],
        "description": (
            "A rigorous three-year, full-time program in anesthesia pharmacology, physiology, and "
            "clinical practice that prepares students for the National Certification Examination "
            "and practice as certified registered nurse anesthetists."
        ),
        "who_its_for": (
            "Critical-care registered nurses pursuing careers as certified registered nurse "
            "anesthetists."
        ),
    },
    {
        "slug": "georgetown-nursing-dnp",
        "school": "School of Nursing",
        "program_name": "Doctor of Nursing Practice",
        "degree_type": "professional",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "online",
        "keywords": ["doctor of nursing practice"],
        "description": (
            "The post-BSN practice doctorate trains nurses for the highest level of advanced "
            "practice across family, adult-gerontology acute care, women's health, and "
            "nurse-midwifery specialties, combining online study with in-person clinical "
            "intensives."
        ),
        "who_its_for": (
            "BSN-prepared registered nurses pursuing a terminal advanced-practice nursing degree."
        ),
    },
    {
        "slug": "georgetown-executive-dnp",
        "school": "School of Nursing",
        "program_name": "Executive Doctor of Nursing Practice",
        "degree_type": "professional",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "online",
        "keywords": ["executive doctor of nursing practice"],
        "description": (
            "A part-time, post-master's practice doctorate that develops nurses already in "
            "advanced roles into systems leaders, focusing on quality improvement, health policy, "
            "and organizational leadership rather than new clinical specialization."
        ),
        "who_its_for": (
            "Nurses who already hold a graduate nursing degree and work in advanced or leadership "
            "roles."
        ),
    },
    {
        "slug": "georgetown-nursing-phd",
        "school": "School of Nursing",
        "program_name": "Doctor of Philosophy in Nursing",
        "degree_type": "phd",
        "department": "School of Nursing",
        "cip": "51.38",
        "delivery_format": "on_campus",
        "keywords": ["nursing"],
        "description": (
            "A full-time research doctorate based at the Capitol Campus that prepares nurse "
            "scientists to generate knowledge and lead change in academic, community-health, "
            "policy, and global research settings."
        ),
        "who_its_for": "Nurses aiming for research, faculty, or scholarly leadership careers.",
    },
    {
        "slug": "georgetown-global-health-bs",
        "school": "School of Health",
        "program_name": "Bachelor of Science in Global Health",
        "degree_type": "bachelors",
        "department": "School of Health",
        "cip": "51.22",
        "delivery_format": "on_campus",
        "keywords": ["global health"],
        "description": (
            "A four-year major blending public health and health-systems management with the "
            "environmental, cultural, economic, and political forces that shape health across "
            "populations and borders."
        ),
        "who_its_for": (
            "Undergraduates drawn to global public health, policy, and the social determinants of "
            "health."
        ),
    },
    {
        "slug": "georgetown-health-care-management-policy-bs",
        "school": "School of Health",
        "program_name": "Bachelor of Science in Health Care Management and Policy",
        "degree_type": "bachelors",
        "department": "School of Health",
        "cip": "51.07",
        "delivery_format": "on_campus",
        "keywords": ["health care management and policy"],
        "description": (
            "This major examines how health systems are organized, financed, and governed, pairing "
            "management and economics with health policy to prepare students to lead and reform "
            "health-care organizations."
        ),
        "who_its_for": (
            "Undergraduates aiming for careers in health-care administration, consulting, or "
            "policy."
        ),
    },
    {
        "slug": "georgetown-human-science-bs",
        "school": "School of Health",
        "program_name": "Bachelor of Science in Human Science",
        "degree_type": "bachelors",
        "department": "School of Health",
        "cip": "30.01",
        "delivery_format": "on_campus",
        "keywords": ["human science"],
        "description": (
            "This major grounds students in molecular and cellular biology, physiology, and "
            "biochemistry within the context of human health, serving as a pre-health foundation "
            "for medicine and biomedical research."
        ),
        "who_its_for": (
            "Pre-med and pre-health undergraduates who want a rigorous science foundation tied to "
            "human health."
        ),
    },
    {
        "slug": "georgetown-global-health-ms",
        "school": "School of Health",
        "program_name": "Master of Science in Global Health",
        "degree_type": "masters",
        "department": "School of Health",
        "cip": "51.22",
        "delivery_format": "on_campus",
        "keywords": ["global health"],
        "description": (
            "This program trains practitioners to address transnational health challenges through "
            "coursework in epidemiology, health policy, and the political and economic systems "
            "driving health inequities, with an accelerated option for Georgetown undergraduates."
        ),
        "who_its_for": (
            "Graduates pursuing careers in global health policy, research, or international health "
            "organizations."
        ),
    },
    {
        "slug": "georgetown-global-infectious-disease-ms",
        "school": "School of Health",
        "program_name": "Master of Science in Global Infectious Disease",
        "degree_type": "masters",
        "department": "School of Health",
        "cip": "51.22",
        "delivery_format": "on_campus",
        "keywords": ["global infectious disease"],
        "description": (
            "This program focuses on the biology, epidemiology, and control of infectious diseases "
            "at a global scale, preparing students to track outbreaks and shape prevention "
            "strategies, with an accelerated pathway available."
        ),
        "who_its_for": (
            "Graduates targeting careers in infectious-disease research, surveillance, and "
            "outbreak response."
        ),
    },
    {
        "slug": "georgetown-health-systems-administration-ms",
        "school": "School of Health",
        "program_name": "Master of Science in Health Systems Administration",
        "degree_type": "masters",
        "department": "School of Health",
        "cip": "51.07",
        "delivery_format": "on_campus",
        "keywords": ["health systems administration"],
        "description": (
            "A CAHME-accredited program developing leaders in health-care operations, finance, and "
            "strategy, equipping graduates to manage hospitals, systems, and other complex "
            "health-care organizations."
        ),
        "who_its_for": (
            "Aspiring health-care executives and administrators seeking a management-focused "
            "graduate degree."
        ),
    },
    {
        "slug": "georgetown-addiction-policy-practice-ms",
        "school": "School of Health",
        "program_name": "Master of Science in Addiction Policy and Practice",
        "degree_type": "masters",
        "department": "School of Health",
        "cip": "51.99",
        "delivery_format": "on_campus",
        "keywords": ["addiction policy and practice"],
        "description": (
            "This program integrates the science of substance use disorders with policy, treatment "
            "systems, and recovery support to prepare professionals who can shape and deliver "
            "effective responses to addiction."
        ),
        "who_its_for": (
            "Professionals working in addiction treatment, recovery services, or substance-use "
            "policy."
        ),
    },
    {
        "slug": "georgetown-climate-environment-health-ms",
        "school": "School of Health",
        "program_name": "Master of Science in Climate, Environment and Health",
        "degree_type": "masters",
        "department": "School of Health",
        "cip": "51.22",
        "delivery_format": "on_campus",
        "keywords": ["climate, environment and health"],
        "description": (
            "Co-led with the Earth Commons Institute, this program examines how climate change and "
            "environmental exposures affect human health and trains students to design adaptation "
            "and mitigation responses."
        ),
        "who_its_for": (
            "Graduates working at the intersection of climate science, environment, and public "
            "health."
        ),
    },
    {
        "slug": "georgetown-clinical-quality-safety-leadership-ms",
        "school": "School of Health",
        "program_name": "Executive Master of Science in Clinical Quality, Safety and Leadership",
        "degree_type": "masters",
        "department": "School of Health",
        "cip": "51.07",
        "delivery_format": "online",
        "keywords": ["clinical quality, safety and leadership"],
        "description": (
            "Offered online with MedStar Health and CAHME-accredited, this program develops "
            "clinical and non-clinical professionals into leaders of patient safety, quality "
            "improvement, and safety-science communication."
        ),
        "who_its_for": (
            "Working health-care professionals advancing into quality, safety, and patient-care "
            "leadership roles."
        ),
    },
    {
        "slug": "georgetown-global-infectious-disease-phd",
        "school": "School of Health",
        "program_name": "Doctor of Philosophy in Global Infectious Disease",
        "degree_type": "phd",
        "department": "School of Health",
        "cip": "51.22",
        "delivery_format": "on_campus",
        "keywords": ["global infectious disease"],
        "description": (
            "A research doctorate, supported by the Department of Global Health, training "
            "scientists to investigate the biology, epidemiology, and control of infectious "
            "diseases threatening global populations."
        ),
        "who_its_for": (
            "Scientists pursuing research and faculty careers in infectious-disease and global "
            "health."
        ),
    },
    {
        "slug": "georgetown-computer-science-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Computer Science",
        "degree_type": "masters",
        "department": "Department of Computer Science",
        "cip": "11.07",
        "delivery_format": "on_campus",
        "keywords": ["computer science"],
        "description": (
            "Core graduate work in algorithms and computer architecture is paired with electives "
            "or a thesis spanning artificial intelligence, security, systems, and theory, "
            "completed as ten courses or eight courses plus research."
        ),
        "who_its_for": (
            "A computing graduate who wants advanced technical depth before an industry or "
            "research career."
        ),
    },
    {
        "slug": "georgetown-computer-science-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Computer Science",
        "degree_type": "phd",
        "department": "Department of Computer Science",
        "cip": "11.07",
        "delivery_format": "on_campus",
        "keywords": ["computer science"],
        "description": (
            "Doctoral students pass core and area qualifying exams, complete a teaching "
            "apprenticeship, and produce an original dissertation in fields such as artificial "
            "intelligence, algorithms, systems, and information security over roughly five funded "
            "years."
        ),
        "who_its_for": (
            "A research-minded student aiming for an academic, industry-research, or government "
            "R&D computing career."
        ),
    },
    {
        "slug": "georgetown-data-science-analytics-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Data Science and Analytics",
        "degree_type": "masters",
        "department": "Data Science and Analytics Program",
        "cip": "30.70",
        "delivery_format": "on_campus",
        "keywords": ["data science and analytics"],
        "description": (
            "A 30-credit interdisciplinary curriculum covers statistical learning, big data and "
            "cloud computing, and data visualization, with specialized tracks in AI, natural "
            "language processing, visualization, and finance."
        ),
        "who_its_for": (
            "An analytically inclined graduate or working professional pursuing a data scientist, "
            "ML engineer, or analytics career."
        ),
    },
    {
        "slug": "georgetown-mathematics-statistics-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Mathematics and Statistics",
        "degree_type": "masters",
        "department": "Department of Mathematics and Statistics",
        "cip": "27.05",
        "delivery_format": "on_campus",
        "keywords": ["mathematics and statistics"],
        "description": (
            "Coursework blends probability, statistical inference, modeling, optimization, and "
            "numerical methods, applied to areas including financial mathematics, biostatistics, "
            "and data science for quantitatively strong students."
        ),
        "who_its_for": (
            "A mathematically prepared graduate heading into data science, finance, or applied "
            "analytics roles."
        ),
    },
    {
        "slug": "georgetown-applied-mathematics-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Applied Mathematics",
        "degree_type": "phd",
        "department": "Department of Mathematics and Statistics",
        "cip": "27.03",
        "delivery_format": "on_campus",
        "keywords": ["applied mathematics"],
        "description": (
            "Doctoral research centers on partial differential equations, calculus of variations, "
            "inverse problems, image processing, and the mathematical-statistical modeling of "
            "biological systems, grounded in core analysis and numerical methods."
        ),
        "who_its_for": (
            "A student pursuing original applied-mathematics research for academia, industry, or "
            "government."
        ),
    },
    {
        "slug": "georgetown-linguistics-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Linguistics",
        "degree_type": "masters",
        "department": "Department of Linguistics",
        "cip": "16.01",
        "delivery_format": "on_campus",
        "keywords": ["linguistics"],
        "description": (
            "Focused graduate study in one of four concentrations—applied, computational, socio-, "
            "or theoretical linguistics—builds specialized expertise in language structure, "
            "acquisition, and variation."
        ),
        "who_its_for": (
            "A language-focused graduate seeking concentrated expertise before professional work "
            "or doctoral study."
        ),
    },
    {
        "slug": "georgetown-linguistics-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Linguistics",
        "degree_type": "phd",
        "department": "Department of Linguistics",
        "cip": "16.01",
        "delivery_format": "on_campus",
        "keywords": ["linguistics"],
        "description": (
            "Three years of coursework across applied, computational, socio-, and theoretical "
            "linguistics precede dissertation research, with an optional secondary concentration "
            "in cognitive science, training scholars of language structure and use."
        ),
        "who_its_for": (
            "A research-oriented student aiming for an academic or research career in linguistics "
            "or computational linguistics."
        ),
    },
    {
        "slug": "georgetown-cct-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in Communication, Culture and Technology",
        "degree_type": "masters",
        "department": "Communication, Culture and Technology Program",
        "cip": "09.01",
        "delivery_format": "on_campus",
        "keywords": ["communication, culture and technology"],
        "description": (
            "An interdisciplinary curriculum examines how media and technology reshape "
            "communication across social, economic, political, and cultural life, pairing critical "
            "theory with hands-on methods and creation."
        ),
        "who_its_for": (
            "An interdisciplinary thinker headed for careers in technology, media, policy, UX, or "
            "research."
        ),
    },
    {
        "slug": "georgetown-english-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in English",
        "degree_type": "masters",
        "department": "Department of English",
        "cip": "23.01",
        "delivery_format": "on_campus",
        "keywords": ["english"],
        "description": (
            "Two-year, thesis-based study spans medieval through contemporary literature alongside "
            "critical theory and fields like cultural studies, gender and sexuality studies, and "
            "film and media, letting students build a chosen sub-field."
        ),
        "who_its_for": (
            "A literature graduate seeking a rigorous terminal master's, often as a springboard to "
            "a doctorate elsewhere."
        ),
    },
    {
        "slug": "georgetown-history-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in Global, International, and Comparative History",
        "degree_type": "masters",
        "department": "Department of History",
        "cip": "54.01",
        "delivery_format": "on_campus",
        "keywords": ["global, international, and comparative history"],
        "description": (
            "The MAGIC program builds a transnational perspective on an interconnected world "
            "through training in historical methods, foreign languages, and research writing "
            "across regional and comparative fields."
        ),
        "who_its_for": (
            "A history graduate wanting advanced research and writing skills with a global, "
            "cross-regional focus."
        ),
    },
    {
        "slug": "georgetown-history-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in History",
        "degree_type": "phd",
        "department": "Department of History",
        "cip": "54.01",
        "delivery_format": "on_campus",
        "keywords": ["history"],
        "description": (
            "Coursework, comprehensive exams, and an original dissertation train historians for "
            "scholarly research and university teaching, with a fully funded package and highly "
            "selective admission."
        ),
        "who_its_for": (
            "An aspiring academic historian committed to original archival research and a "
            "dissertation."
        ),
    },
    {
        "slug": "georgetown-philosophy-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Philosophy",
        "degree_type": "phd",
        "department": "Department of Philosophy",
        "cip": "38.01",
        "delivery_format": "on_campus",
        "keywords": ["philosophy"],
        "description": (
            "Doctoral research concentrates in ethical theory and practical ethics including "
            "bioethics, social and political philosophy, philosophy of language, epistemology, "
            "modern European philosophy, and the Catholic philosophical tradition."
        ),
        "who_its_for": (
            "A philosophy graduate pursuing an academic research career, especially in ethics or "
            "the history of philosophy."
        ),
    },
    {
        "slug": "georgetown-theology-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Theological and Religious Studies",
        "degree_type": "phd",
        "department": "Department of Theology and Religious Studies",
        "cip": "38.02",
        "delivery_format": "on_campus",
        "keywords": ["theological and religious studies"],
        "description": (
            "An interdisciplinary doctorate for the critical, comparative study of theology and "
            "religion draws on faculty across Christianity, Islam, Judaism, Hinduism, Buddhism, "
            "and Confucianism, emphasizing interreligious understanding and pluralism."
        ),
        "who_its_for": (
            "A scholar holding a master's in theology or religious studies who seeks a research "
            "doctorate in comparative religion."
        ),
    },
    {
        "slug": "georgetown-german-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in German",
        "degree_type": "masters",
        "department": "Department of German",
        "cip": "16.05",
        "delivery_format": "on_campus",
        "keywords": ["german"],
        "description": (
            "Graduate study of German literature, culture, and language from the eighteenth "
            "century to the present applies critical and interdisciplinary approaches in "
            "preparation for research and teaching."
        ),
        "who_its_for": (
            "A student of German language and culture seeking advanced training before or instead "
            "of doctoral work."
        ),
    },
    {
        "slug": "georgetown-german-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in German",
        "degree_type": "phd",
        "department": "Department of German",
        "cip": "16.05",
        "delivery_format": "on_campus",
        "keywords": ["german"],
        "description": (
            "Doctoral research engages German literary and cultural history from the eighteenth "
            "century onward through specialized, interdisciplinary inquiry, structured for "
            "completion within roughly five years."
        ),
        "who_its_for": (
            "An advanced Germanist aiming for a research and teaching career in German studies."
        ),
    },
    {
        "slug": "georgetown-spanish-linguistics-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Spanish Linguistics",
        "degree_type": "masters",
        "department": "Department of Spanish and Portuguese",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["spanish linguistics"],
        "description": (
            "Graduate coursework examines the structure, acquisition, and social variation of the "
            "Spanish language through formal and applied linguistic methods grounded in the "
            "Hispanic world."
        ),
        "who_its_for": (
            "A student of Spanish wanting analytical, linguistics-focused graduate training."
        ),
    },
    {
        "slug": "georgetown-spanish-linguistics-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Spanish Linguistics",
        "degree_type": "phd",
        "department": "Department of Spanish and Portuguese",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["spanish linguistics"],
        "description": (
            "Doctoral research investigates Spanish phonology, syntax, sociolinguistics, and "
            "second-language acquisition, preparing scholars for academic careers in Hispanic "
            "linguistics."
        ),
        "who_its_for": (
            "A researcher pursuing an academic career in Spanish or Hispanic linguistics."
        ),
    },
    {
        "slug": "georgetown-spanish-literature-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Spanish Literature and Cultural Studies",
        "degree_type": "masters",
        "department": "Department of Spanish and Portuguese",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["spanish literature and cultural studies"],
        "description": (
            "Graduate study explores Peninsular and Latin American literature and cultural "
            "production through close literary analysis and cultural theory across the Hispanic "
            "world."
        ),
        "who_its_for": (
            "A student of Hispanic literature and culture seeking advanced humanistic graduate "
            "training."
        ),
    },
    {
        "slug": "georgetown-spanish-literature-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Spanish Literature and Cultural Studies",
        "degree_type": "phd",
        "department": "Department of Spanish and Portuguese",
        "cip": "16.09",
        "delivery_format": "on_campus",
        "keywords": ["spanish literature and cultural studies"],
        "description": (
            "Doctoral research engages Peninsular and Latin American literatures and cultural "
            "studies, training scholars to produce original criticism and teach Hispanic literary "
            "and cultural history."
        ),
        "who_its_for": "An aspiring academic in Hispanic literary and cultural studies.",
    },
    {
        "slug": "georgetown-arabic-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in Arabic and Islamic Studies",
        "degree_type": "masters",
        "department": "Department of Arabic and Islamic Studies",
        "cip": "16.11",
        "delivery_format": "on_campus",
        "keywords": ["arabic and islamic studies"],
        "description": (
            "Graduate training in the languages, literatures, and thought of the Islamic world "
            "emphasizes Arabic textual traditions, with a concentration in Arabic Literature, "
            "Arabic Linguistics, or Islamic Studies."
        ),
        "who_its_for": (
            "A student with strong Arabic preparation seeking graduate study of Arabic and Islamic "
            "intellectual traditions."
        ),
    },
    {
        "slug": "georgetown-arabic-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Arabic and Islamic Studies",
        "degree_type": "phd",
        "department": "Department of Arabic and Islamic Studies",
        "cip": "16.11",
        "delivery_format": "on_campus",
        "keywords": ["arabic and islamic studies"],
        "description": (
            "Advanced doctoral training in Arabic linguistics, classical and modern Arabic "
            "literature, and Islamic intellectual history, theology, and law centers on the close "
            "reading of primary sources."
        ),
        "who_its_for": (
            "A scholar pursuing an academic career in Arabic linguistics, literature, or Islamic "
            "studies."
        ),
    },
    {
        "slug": "georgetown-applied-economics-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in Applied Economics",
        "degree_type": "masters",
        "department": "Department of Economics",
        "cip": "45.06",
        "delivery_format": "on_campus",
        "keywords": ["applied economics"],
        "description": (
            "Training in the core tools of economic analysis is applied to rigorous, data-driven "
            "evaluation of real-world economic issues and public-policy questions from a base in "
            "Washington, DC."
        ),
        "who_its_for": (
            "A professional or recent graduate wanting applied, policy-oriented economic analysis "
            "without a research doctorate."
        ),
    },
    {
        "slug": "georgetown-economics-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Economics",
        "degree_type": "phd",
        "department": "Department of Economics",
        "cip": "45.06",
        "delivery_format": "on_campus",
        "keywords": ["economics"],
        "description": (
            "A research-intensive 54-credit doctorate prepares scholars to work at the frontier of "
            "economic science, well situated in the capital for both pure theory and "
            "policy-informed research."
        ),
        "who_its_for": (
            "An aspiring research economist or academic pursuing scholarly or advanced "
            "policy-research work."
        ),
    },
    {
        "slug": "georgetown-american-government-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in American Government",
        "degree_type": "masters",
        "department": "Department of Government",
        "cip": "45.10",
        "delivery_format": "on_campus",
        "keywords": ["american government"],
        "description": (
            "An accelerated twelve-month program covers U.S. political institutions, electoral "
            "politics, public opinion, parties, and quantitative methods, paired with an "
            "eight-month hands-on practicum in Washington, DC."
        ),
        "who_its_for": (
            "A motivated student pursuing careers in public service, electoral politics, or "
            "government consulting."
        ),
    },
    {
        "slug": "georgetown-conflict-resolution-ma",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Arts in Conflict Resolution",
        "degree_type": "masters",
        "department": "Department of Government",
        "cip": "30.05",
        "delivery_format": "on_campus",
        "keywords": ["conflict resolution"],
        "description": (
            "A 34-credit peace-and-conflict program taught by scholar-practitioners covers "
            "conflict analysis, prevention, peacemaking, peacekeeping, peacebuilding, and "
            "nonviolence, including a summer of fieldwork."
        ),
        "who_its_for": (
            "A student seeking theoretical and practical training to manage conflict in policy, "
            "diplomacy, or NGO careers."
        ),
    },
    {
        "slug": "georgetown-government-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Government",
        "degree_type": "phd",
        "department": "Department of Government",
        "cip": "45.10",
        "delivery_format": "on_campus",
        "keywords": ["government"],
        "description": (
            "Organized around American government, comparative government, international "
            "relations, and political theory, the doctorate builds the analytical and "
            "methodological skills to produce original political-science research."
        ),
        "who_its_for": (
            "A student aiming for scholarly research and university-level teaching in political "
            "science."
        ),
    },
    {
        "slug": "georgetown-psychology-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Psychology",
        "degree_type": "phd",
        "department": "Department of Psychology",
        "cip": "42.01",
        "delivery_format": "on_campus",
        "keywords": ["psychology"],
        "description": (
            "A fully funded research doctorate concentrating in either Human Development and "
            "Public Policy or Lifespan Cognitive Neuroscience studies learning, cognition, "
            "emotion, and behavior and their neural basis across the lifespan."
        ),
        "who_its_for": (
            "A research-focused student pursuing developmental or cognitive-neuroscience "
            "scholarship in a program with no clinical track."
        ),
    },
    {
        "slug": "georgetown-biology-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Biology",
        "degree_type": "phd",
        "department": "Department of Biology",
        "cip": "26.01",
        "delivery_format": "on_campus",
        "keywords": ["biology"],
        "description": (
            "Doctoral candidates pursue original research across the biological sciences, from "
            "molecular and cellular mechanisms to evolution and ecology, over roughly five years "
            "of mentored lab work and a defended dissertation."
        ),
        "who_its_for": (
            "A research-focused student wanting a fully funded, dissertation-driven biology "
            "doctorate."
        ),
    },
    {
        "slug": "georgetown-physics-ms",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Master of Science in Physics",
        "degree_type": "masters",
        "department": "Department of Physics",
        "cip": "40.08",
        "delivery_format": "on_campus",
        "keywords": ["physics"],
        "description": (
            "Coursework-centered training in experimental and theoretical physics is offered in "
            "thesis and non-thesis tracks for students consolidating advanced fundamentals before "
            "industry or further study."
        ),
        "who_its_for": (
            "A physics graduate wanting an advanced master's for technical industry roles or as a "
            "bridge to doctoral study."
        ),
    },
    {
        "slug": "georgetown-physics-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Physics",
        "degree_type": "phd",
        "department": "Department of Physics",
        "cip": "40.08",
        "delivery_format": "on_campus",
        "keywords": ["physics"],
        "description": (
            "Advanced coursework accompanies sustained original research alongside internationally "
            "recognized experimental and theoretical groups in areas such as condensed-matter, "
            "biophysics, and gravitation, culminating in a defended dissertation over a funded "
            "five-year program."
        ),
        "who_its_for": (
            "A physics graduate committed to independent doctoral research with funded support."
        ),
    },
    {
        "slug": "georgetown-chemistry-phd",
        "school": "Graduate School of Arts & Sciences",
        "program_name": "Doctor of Philosophy in Chemistry",
        "degree_type": "phd",
        "department": "Department of Chemistry",
        "cip": "40.05",
        "delivery_format": "on_campus",
        "keywords": ["chemistry"],
        "description": (
            "Students begin original research in their first year across organic, inorganic, "
            "physical, analytical, computational, materials, and biological chemistry, completing "
            "coursework, seminars, and a dissertation."
        ),
        "who_its_for": (
            "A chemistry graduate seeking a research career in academia, industry, or government."
        ),
    },
    {
        "slug": "georgetown-public-policy-mpp",
        "school": "McCourt School of Public Policy",
        "program_name": "Master of Public Policy",
        "degree_type": "masters",
        "department": "McCourt School of Public Policy",
        "cip": "44.05",
        "delivery_format": "on_campus",
        "keywords": ["master of public policy"],
        "description": (
            "A 48-credit core curriculum in microeconomics, quantitative methods, politics, and "
            "management trains students to design, analyze, and implement evidence-based policy "
            "through a two-semester applied capstone."
        ),
        "who_its_for": (
            "Aspiring policy analysts and advisors who want rigorous analytic and management "
            "training to shape public decisions."
        ),
    },
    {
        "slug": "georgetown-data-science-public-policy-ms",
        "school": "McCourt School of Public Policy",
        "program_name": "Master of Science in Data Science for Public Policy",
        "degree_type": "masters",
        "department": "McCourt School of Public Policy",
        "cip": "44.05",
        "delivery_format": "on_campus",
        "keywords": ["data science for public policy"],
        "description": (
            "A 39-credit program pairing McCourt's policy-analysis core with machine learning, "
            "statistical programming, and data engineering so graduates can turn large public "
            "datasets into actionable policy insight."
        ),
        "who_its_for": (
            "Quantitatively inclined students aiming for data-driven analyst roles across "
            "government, nonprofits, and civic tech."
        ),
    },
    {
        "slug": "georgetown-international-development-policy-midp",
        "school": "McCourt School of Public Policy",
        "program_name": "Master of International Development Policy",
        "degree_type": "masters",
        "department": "McCourt School of Public Policy",
        "cip": "44.05",
        "delivery_format": "on_campus",
        "keywords": ["master of international development policy"],
        "description": (
            "A 48-credit course of study in development economics, governance, and global poverty, "
            "culminating in a summer professional placement and capstone addressing real "
            "challenges in low- and middle-income countries."
        ),
        "who_its_for": (
            "Future development practitioners working with international agencies, NGOs, and "
            "governments on global poverty and growth."
        ),
    },
    {
        "slug": "georgetown-policy-management-mpm",
        "school": "McCourt School of Public Policy",
        "program_name": "Master of Policy Management",
        "degree_type": "masters",
        "department": "McCourt School of Public Policy",
        "cip": "44.04",
        "delivery_format": "on_campus",
        "keywords": ["master of policy management"],
        "description": (
            "An accelerated program for mid-career professionals balancing analytics, management, "
            "and substantive policy fields to sharpen the leadership and quantitative skills "
            "needed for senior public-sector advancement."
        ),
        "who_its_for": (
            "Experienced professionals with roughly five or more years in policy seeking "
            "accelerated mid-career advancement."
        ),
    },
    {
        "slug": "georgetown-policy-leadership-empl",
        "school": "McCourt School of Public Policy",
        "program_name": "Executive Master of Policy Leadership",
        "degree_type": "masters",
        "department": "McCourt School of Public Policy",
        "cip": "44.04",
        "delivery_format": "hybrid",
        "keywords": ["executive master of policy leadership"],
        "description": (
            "An executive-format program building advanced leadership, strategy, and analytic "
            "capacity for working professionals who direct policy and manage organizations in "
            "government, advocacy, and the private sector."
        ),
        "who_its_for": (
            "Senior working professionals leading policy organizations who need executive-paced "
            "graduate study."
        ),
    },
    {
        "slug": "georgetown-applied-intelligence-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Applied Intelligence",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "29.02",
        "delivery_format": "online",
        "keywords": ["applied intelligence"],
        "description": (
            "This program covers the intelligence cycle, collection and analytic tradecraft, and "
            "emerging technologies so students can support national-security, law-enforcement, and "
            "corporate intelligence operations in a data-saturated environment."
        ),
        "who_its_for": (
            "Analysts and officers building careers in national-security, competitive, or "
            "corporate intelligence."
        ),
    },
    {
        "slug": "georgetown-ai-management-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Artificial Intelligence Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "11.01",
        "delivery_format": "online",
        "keywords": ["artificial intelligence management"],
        "description": (
            "This program blends machine-learning fundamentals with governance, ethics, and "
            "applied leadership so managers can evaluate, deploy, and oversee AI systems "
            "responsibly within their organizations."
        ),
        "who_its_for": (
            "Managers and technologists who must lead AI adoption rather than build models from "
            "scratch."
        ),
    },
    {
        "slug": "georgetown-cybersecurity-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Cybersecurity Risk Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "11.10",
        "delivery_format": "online",
        "keywords": ["cybersecurity risk management"],
        "description": (
            "This program focuses on the governance, policy, and risk-management side of "
            "cybersecurity, teaching professionals to assess threats, build frameworks, and align "
            "security strategy with organizational and regulatory demands."
        ),
        "who_its_for": (
            "Security and risk professionals moving into cybersecurity leadership and governance "
            "roles."
        ),
    },
    {
        "slug": "georgetown-design-management-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Design Management and Communications",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "50.04",
        "delivery_format": "online",
        "keywords": ["design management and communications"],
        "description": (
            "This program combines design thinking, brand strategy, and communications management "
            "so professionals can lead creative teams and translate user-centered design into "
            "measurable business and organizational outcomes."
        ),
        "who_its_for": (
            "Creative and communications professionals stepping into design-leadership and "
            "strategy roles."
        ),
    },
    {
        "slug": "georgetown-emergency-disaster-management-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Emergency and Disaster Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "43.02",
        "delivery_format": "hybrid",
        "keywords": ["emergency and disaster management"],
        "description": (
            "This program trains professionals in preparedness, mitigation, response, and recovery "
            "across natural and human-caused crises, integrating policy, logistics, and continuity "
            "planning for public agencies and private organizations."
        ),
        "who_its_for": (
            "First responders and managers building careers in emergency, homeland-security, and "
            "continuity management."
        ),
    },
    {
        "slug": "georgetown-global-sports-mps",
        "school": "School of Continuing Studies",
        "program_name": (
            "Executive Master of Professional Studies in Global Sports Operations and Strategy"
        ),
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "31.05",
        "delivery_format": "hybrid",
        "keywords": ["global sports operations and strategy"],
        "description": (
            "An executive program examining international sport business, club operations, and "
            "commercial strategy, delivered online with in-person residencies that immerse leaders "
            "in the global sports industry."
        ),
        "who_its_for": (
            "Experienced sports-industry executives expanding into global operations and strategy "
            "leadership."
        ),
    },
    {
        "slug": "georgetown-higher-education-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Higher Education Administration",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "13.04",
        "delivery_format": "online",
        "keywords": ["higher education administration"],
        "description": (
            "This program examines enrollment, student affairs, finance, and policy in colleges "
            "and universities, preparing administrators to manage operations and lead change "
            "across the higher-education landscape."
        ),
        "who_its_for": (
            "Student-affairs and administrative staff advancing into higher-education leadership "
            "roles."
        ),
    },
    {
        "slug": "georgetown-human-resources-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Human Resources Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "52.10",
        "delivery_format": "online",
        "keywords": ["human resources management"],
        "description": (
            "This program develops competencies in talent strategy, organizational development, "
            "employment law, and analytics so HR professionals can act as strategic business "
            "partners shaping workforce and culture decisions."
        ),
        "who_its_for": (
            "HR practitioners moving from administration toward strategic talent leadership."
        ),
    },
    {
        "slug": "georgetown-it-management-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Information Technology Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "52.12",
        "delivery_format": "online",
        "keywords": ["information technology management"],
        "description": (
            "This program bridges technical systems and business strategy, covering IT governance, "
            "enterprise architecture, and project delivery so professionals can lead technology "
            "organizations and digital transformation."
        ),
        "who_its_for": (
            "IT professionals advancing toward CIO-track and technology-leadership positions."
        ),
    },
    {
        "slug": "georgetown-integrated-marketing-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Integrated Marketing Communications",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "09.09",
        "delivery_format": "online",
        "keywords": ["integrated marketing communications"],
        "description": (
            "This program centers on data-informed brand strategy, digital channels, and audience "
            "analytics, teaching marketers to design and measure coordinated campaigns across "
            "paid, owned, and earned media."
        ),
        "who_its_for": (
            "Marketing and communications professionals building data-driven brand and campaign "
            "expertise."
        ),
    },
    {
        "slug": "georgetown-journalism-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Journalism",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "09.04",
        "delivery_format": "on_campus",
        "keywords": ["journalism"],
        "description": (
            "This program emphasizes reporting, multimedia storytelling, and ethics in a "
            "Washington, DC newsroom setting, training journalists to produce rigorous work across "
            "digital, audio, and visual formats."
        ),
        "who_its_for": (
            "Emerging and career-changing journalists seeking hands-on reporting training in the "
            "capital."
        ),
    },
    {
        "slug": "georgetown-project-management-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Project Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "52.02",
        "delivery_format": "online",
        "keywords": ["project management"],
        "description": (
            "This program covers scope, scheduling, risk, and stakeholder leadership across "
            "predictive and agile methods so professionals can plan and deliver complex projects "
            "on time and on budget."
        ),
        "who_its_for": (
            "Professionals leading complex projects who want formal credentialing and leadership "
            "skills."
        ),
    },
    {
        "slug": "georgetown-public-relations-mps",
        "school": "School of Continuing Studies",
        "program_name": (
            "Master of Professional Studies in Public Relations and Corporate Communications"
        ),
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "09.09",
        "delivery_format": "online",
        "keywords": ["public relations and corporate communications"],
        "description": (
            "This program focuses on reputation management, crisis communication, and stakeholder "
            "strategy, preparing communicators to shape narratives and protect brands across "
            "corporate, nonprofit, and government settings."
        ),
        "who_its_for": (
            "Communications professionals advancing into PR and corporate-communications "
            "leadership."
        ),
    },
    {
        "slug": "georgetown-real-estate-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Real Estate",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "52.15",
        "delivery_format": "online",
        "keywords": ["real estate"],
        "description": (
            "This program spans development, finance, investment, and market analysis across the "
            "real-estate lifecycle, training professionals to underwrite deals and manage projects "
            "from acquisition through disposition."
        ),
        "who_its_for": (
            "Real-estate and finance professionals moving into development and investment roles."
        ),
    },
    {
        "slug": "georgetown-sports-industry-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Sports Industry Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "31.05",
        "delivery_format": "online",
        "keywords": ["sports industry management"],
        "description": (
            "This program examines sport business operations, marketing, finance, and governance, "
            "preparing professionals to manage teams, leagues, venues, and brands across the "
            "commercial sports ecosystem."
        ),
        "who_its_for": (
            "Professionals pursuing management careers across teams, leagues, and sports brands."
        ),
    },
    {
        "slug": "georgetown-supply-chain-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Supply Chain Management",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "52.03",
        "delivery_format": "online",
        "keywords": ["supply chain management"],
        "description": (
            "This program covers logistics, procurement, operations analytics, and resilience so "
            "professionals can design and manage efficient, transparent supply chains amid global "
            "disruption and rising complexity."
        ),
        "who_its_for": (
            "Operations and logistics professionals advancing into supply-chain leadership."
        ),
    },
    {
        "slug": "georgetown-urban-planning-mps",
        "school": "School of Continuing Studies",
        "program_name": "Master of Professional Studies in Urban and Regional Planning",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "04.03",
        "delivery_format": "on_campus",
        "keywords": ["urban and regional planning"],
        "description": (
            "This program integrates land use, transportation, housing, and sustainability with "
            "planning law and community engagement so students can shape equitable, resilient "
            "cities and regions."
        ),
        "who_its_for": (
            "Future planners and policy practitioners shaping land use and community development."
        ),
    },
    {
        "slug": "georgetown-liberal-studies-bals",
        "school": "School of Continuing Studies",
        "program_name": "Bachelor of Arts in Liberal Studies",
        "degree_type": "bachelors",
        "department": "School of Continuing Studies",
        "cip": "24.01",
        "delivery_format": "hybrid",
        "keywords": ["liberal studies"],
        "description": (
            "An interdisciplinary degree-completion program drawing on the humanities, social "
            "sciences, and arts, letting adult students design a broad, integrative course of "
            "study toward the bachelor's degree."
        ),
        "who_its_for": (
            "Returning adult learners completing an interdisciplinary undergraduate degree."
        ),
    },
    {
        "slug": "georgetown-liberal-studies-mals",
        "school": "School of Continuing Studies",
        "program_name": "Master of Arts in Liberal Studies",
        "degree_type": "masters",
        "department": "School of Continuing Studies",
        "cip": "24.01",
        "delivery_format": "hybrid",
        "keywords": ["liberal studies"],
        "description": (
            "An interdisciplinary graduate program in the humanities and social sciences "
            "culminating in a faculty-directed thesis, letting students pursue intellectually "
            "serious inquiry across traditional disciplinary boundaries."
        ),
        "who_its_for": (
            "Intellectually curious professionals seeking interdisciplinary graduate study and a "
            "research thesis."
        ),
    },
    {
        "slug": "georgetown-liberal-studies-dls",
        "school": "School of Continuing Studies",
        "program_name": "Doctor of Liberal Studies",
        "degree_type": "professional",
        "department": "School of Continuing Studies",
        "cip": "24.01",
        "delivery_format": "on_campus",
        "keywords": ["doctor of liberal studies"],
        "description": (
            "An interdisciplinary doctoral program grounded in philosophy, theology, history, "
            "literature, and the social sciences, culminating in a rigorous thesis that "
            "demonstrates scholarly competence across fields."
        ),
        "who_its_for": (
            "Accomplished professionals pursuing advanced interdisciplinary scholarship at the "
            "doctoral level."
        ),
    },
    {
        "slug": "georgetown-jd",
        "school": "Georgetown University Law Center",
        "program_name": "Juris Doctor",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.01",
        "delivery_format": "on_campus",
        "keywords": ["juris doctor"],
        "description": (
            "A three-year professional program built on the largest law curriculum in the United "
            "States, pairing a foundational first-year doctrinal core with deep electives, "
            "clinics, and externships across the federal courts, agencies, and Congress."
        ),
        "who_its_for": (
            "College graduates seeking to become practicing attorneys with access to government, "
            "public-interest, and private-sector law in the nation's capital."
        ),
    },
    {
        "slug": "georgetown-llm-taxation",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in Taxation",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["taxation"],
        "description": (
            "Advanced study of federal tax law spanning corporate, partnership, international, and "
            "estate taxation draws on the nation's most extensive graduate tax curriculum and "
            "proximity to the IRS, Treasury, and the Tax Court."
        ),
        "who_its_for": (
            "Practicing lawyers specializing in tax who want elite-level expertise in federal and "
            "international tax law."
        ),
    },
    {
        "slug": "georgetown-llm-international-business",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in International Business and Economic Law",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["international business and economic law"],
        "description": (
            "Focused training in cross-border transactions, trade regulation, international "
            "finance, and the legal frameworks governing the global economy is taught alongside "
            "Georgetown's institutes on trade and international economic law."
        ),
        "who_its_for": (
            "Lawyers building careers in international commerce, trade, or financial regulation "
            "across jurisdictions."
        ),
    },
    {
        "slug": "georgetown-llm-national-security",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in National Security Law",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["national security law"],
        "description": (
            "Concentrated study of the constitutional, statutory, and international law governing "
            "intelligence, armed conflict, counterterrorism, and homeland security leverages "
            "Georgetown's national-security faculty and government connections."
        ),
        "who_its_for": (
            "Lawyers entering or advancing in defense, intelligence, foreign-policy, or "
            "homeland-security legal practice."
        ),
    },
    {
        "slug": "georgetown-llm-environmental-energy",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in Environmental and Energy Law",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["environmental and energy law"],
        "description": (
            "Specialized examination of pollution control, climate, natural-resource, and energy "
            "regulation is grounded in the federal administrative and regulatory practice centered "
            "in Washington, DC."
        ),
        "who_its_for": (
            "Lawyers focusing on environmental regulation, energy markets, or climate and "
            "natural-resource law."
        ),
    },
    {
        "slug": "georgetown-llm-global-health",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in National and Global Health Law",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["national and global health law"],
        "description": (
            "Study of the domestic and international legal regimes shaping public health, "
            "healthcare regulation, bioethics, and global health governance is anchored by the "
            "O'Neill Institute for National and Global Health Law."
        ),
        "who_its_for": (
            "Lawyers working in health policy, healthcare regulation, or international "
            "public-health law."
        ),
    },
    {
        "slug": "georgetown-llm-international-legal-studies",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in International Legal Studies",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["international legal studies"],
        "description": (
            "A broad graduate program in public and private international law, comparative law, "
            "human rights, and transnational legal systems for lawyers seeking grounding in the "
            "global legal order."
        ),
        "who_its_for": (
            "Foreign-educated and U.S. lawyers seeking a wide-ranging foundation in international "
            "and comparative law."
        ),
    },
    {
        "slug": "georgetown-llm-technology-law",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in Technology Law and Policy",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["technology law and policy"],
        "description": (
            "Advanced coursework on privacy, data governance, intellectual property, "
            "cybersecurity, and the regulation of emerging technologies is situated near the "
            "federal agencies that shape U.S. technology policy."
        ),
        "who_its_for": (
            "Lawyers specializing in privacy, intellectual property, cybersecurity, or technology "
            "regulation."
        ),
    },
    {
        "slug": "georgetown-llm-general",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Laws in General Studies",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["general studies"],
        "description": (
            "An individualized degree that lets students design their own course of advanced legal "
            "study across the full graduate curriculum rather than committing to a single named "
            "specialization."
        ),
        "who_its_for": (
            "Lawyers who want to tailor an advanced legal program across multiple fields rather "
            "than one concentration."
        ),
    },
    {
        "slug": "georgetown-mlt",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Law and Technology",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["master of law and technology"],
        "description": (
            "A degree for non-lawyers that builds working fluency in how law, regulation, and "
            "policy govern technology, covering privacy, intellectual property, and digital "
            "governance without preparing students for bar admission."
        ),
        "who_its_for": (
            "Technologists, policy professionals, and others without a law degree who need to "
            "navigate the technology-law landscape."
        ),
    },
    {
        "slug": "georgetown-msl-taxation",
        "school": "Georgetown University Law Center",
        "program_name": "Master of Studies in Law in Taxation",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "online",
        "keywords": ["taxation"],
        "description": (
            "An online program letting experienced tax professionals who are not attorneys take "
            "Georgetown's advanced tax courses, providing high-level study of federal tax law "
            "without qualifying graduates to practice law."
        ),
        "who_its_for": (
            "Experienced non-attorney tax professionals seeking advanced tax-law training."
        ),
    },
    {
        "slug": "georgetown-sjd",
        "school": "Georgetown University Law Center",
        "program_name": "Doctor of Juridical Science",
        "degree_type": "professional",
        "department": "Georgetown University Law Center",
        "cip": "22.02",
        "delivery_format": "on_campus",
        "keywords": ["doctor of juridical science"],
        "description": (
            "The Law Center's highest degree centers on an original, book-length dissertation "
            "written through intensive multi-year legal research under a faculty supervisor, "
            "preparing graduates for legal scholarship and teaching."
        ),
        "who_its_for": (
            "Lawyers, typically with a master's in law, aiming for academic careers as legal "
            "scholars and law professors."
        ),
    },
    {
        "slug": "georgetown-md",
        "school": "School of Medicine",
        "program_name": "Doctor of Medicine",
        "degree_type": "professional",
        "department": "School of Medicine",
        "cip": "51.12",
        "delivery_format": "on_campus",
        "keywords": ["doctor of medicine"],
        "description": (
            "A four-year program built on the Journeys Curriculum, moving from foundational "
            "science through a 48-week core clerkship year and an advanced clinical phase, with a "
            "required mentored scholarly project for graduation."
        ),
        "who_its_for": (
            "Aspiring physicians seeking a Jesuit-grounded, patient-centered medical education in "
            "Washington, DC."
        ),
    },
    {
        "slug": "georgetown-physiology-biophysics-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Physiology and Biophysics",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.09",
        "delivery_format": "on_campus",
        "keywords": ["physiology and biophysics"],
        "description": (
            "Graduate study of how organ systems and cellular mechanisms function and are "
            "regulated combines physiology coursework with biophysical principles and research "
            "within the medical center."
        ),
        "who_its_for": (
            "Students seeking research depth in physiology or strengthening credentials for "
            "medical and health-professional schools."
        ),
    },
    {
        "slug": "georgetown-physiology-smp-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Physiology and Biophysics (Special Master's Program)",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.09",
        "delivery_format": "on_campus",
        "keywords": ["physiology and biophysics (special master's program)"],
        "description": (
            "A one-year postbaccalaureate program in which students take first-year medical-school "
            "physiology coursework to demonstrate readiness for the rigor of medical and other "
            "health-professional schools."
        ),
        "who_its_for": (
            "Pre-health applicants who need to strengthen their academic record before applying to "
            "medical school."
        ),
    },
    {
        "slug": "georgetown-pharmacology-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Pharmacology",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.10",
        "delivery_format": "on_campus",
        "keywords": ["pharmacology"],
        "description": (
            "Study of how drugs act on biological systems spans molecular drug mechanisms, "
            "receptor signaling, toxicology, and therapeutic development, with laboratory research "
            "at Georgetown University Medical Center."
        ),
        "who_its_for": (
            "Students pursuing research or industry careers in drug discovery, or strengthening "
            "pre-health credentials."
        ),
    },
    {
        "slug": "georgetown-biochemistry-molecular-biology-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Biochemistry and Molecular Biology",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.02",
        "delivery_format": "on_campus",
        "keywords": ["biochemistry and molecular biology"],
        "description": (
            "Advanced training in the molecular machinery of the cell covers gene expression, "
            "protein structure and function, and metabolic regulation through coursework and bench "
            "research."
        ),
        "who_its_for": (
            "Students aiming for research careers or doctoral study in the molecular life sciences."
        ),
    },
    {
        "slug": "georgetown-microbiology-immunology-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Microbiology and Immunology",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.05",
        "delivery_format": "on_campus",
        "keywords": ["microbiology and immunology"],
        "description": (
            "Examination of microbial pathogens, host defense, and the immune system integrates "
            "coursework on infectious disease and immunity with hands-on laboratory research."
        ),
        "who_its_for": (
            "Students preparing for research, health-professional school, or doctoral work in "
            "infection and immunity."
        ),
    },
    {
        "slug": "georgetown-tumor-biology-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Tumor Biology",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.02",
        "delivery_format": "on_campus",
        "keywords": ["tumor biology"],
        "description": (
            "Focused study of the cellular and molecular basis of cancer, including oncogenesis, "
            "the tumor microenvironment, and therapeutics, is connected to the Lombardi "
            "Comprehensive Cancer Center."
        ),
        "who_its_for": (
            "Students pursuing cancer research careers or doctoral study in oncology-related "
            "sciences."
        ),
    },
    {
        "slug": "georgetown-biotechnology-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Biotechnology",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.12",
        "delivery_format": "hybrid",
        "keywords": ["biotechnology"],
        "description": (
            "Training that bridges molecular life science with the business, regulatory, and "
            "commercialization aspects of the biotechnology industry is available in an online "
            "format for working professionals."
        ),
        "who_its_for": (
            "Students and professionals seeking careers in biotech research, management, or "
            "product development."
        ),
    },
    {
        "slug": "georgetown-biostatistics-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Biostatistics",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.11",
        "delivery_format": "on_campus",
        "keywords": ["biostatistics"],
        "description": (
            "Quantitative training in the statistical design and analysis of biomedical and "
            "clinical studies covers experimental design, survival analysis, and statistical "
            "computing for health research."
        ),
        "who_its_for": (
            "Quantitatively inclined students preparing for careers analyzing biomedical and "
            "public-health data."
        ),
    },
    {
        "slug": "georgetown-bioinformatics-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Bioinformatics",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.11",
        "delivery_format": "on_campus",
        "keywords": ["bioinformatics"],
        "description": (
            "Computational study of biological data integrates programming, genomics, and "
            "statistical methods to analyze sequences, structures, and large-scale molecular "
            "datasets."
        ),
        "who_its_for": (
            "Students bridging computer science and biology for careers in computational and "
            "data-driven life science."
        ),
    },
    {
        "slug": "georgetown-clinical-translational-research-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Clinical and Translational Research",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "51.99",
        "delivery_format": "on_campus",
        "keywords": ["clinical and translational research"],
        "description": (
            "Methodological training in moving discoveries from bench to bedside covers "
            "clinical-trial design, epidemiology, biostatistics, and the conduct of "
            "patient-oriented research."
        ),
        "who_its_for": (
            "Physicians and researchers building skills to design and lead clinical and "
            "translational studies."
        ),
    },
    {
        "slug": "georgetown-systems-medicine-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Systems Medicine",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.01",
        "delivery_format": "on_campus",
        "keywords": ["systems medicine"],
        "description": (
            "An integrative approach treating the body as interconnected networks combines "
            "genomics, computational modeling, and physiology to understand disease at a systems "
            "level for precision-medicine applications."
        ),
        "who_its_for": (
            "Students seeking a holistic, data-driven foundation in disease biology and precision "
            "medicine."
        ),
    },
    {
        "slug": "georgetown-integrative-medicine-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Integrative Medicine and Health Sciences",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "51.33",
        "delivery_format": "on_campus",
        "keywords": ["integrative medicine and health sciences"],
        "description": (
            "Study of evidence-based complementary and integrative approaches to health alongside "
            "core biomedical sciences examines nutrition, mind-body practices, and whole-person "
            "care."
        ),
        "who_its_for": (
            "Students and clinicians interested in integrative, whole-person approaches grounded "
            "in biomedical science."
        ),
    },
    {
        "slug": "georgetown-integrative-neuroscience-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Integrative Neuroscience",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.15",
        "delivery_format": "on_campus",
        "keywords": ["integrative neuroscience"],
        "description": (
            "Study of the nervous system spanning molecular, cellular, systems, and cognitive "
            "levels integrates neurobiology coursework with research into brain function and "
            "disease."
        ),
        "who_its_for": (
            "Students preparing for doctoral study or careers in neuroscience research and health "
            "professions."
        ),
    },
    {
        "slug": "georgetown-biohazardous-threat-ms",
        "school": "School of Medicine",
        "program_name": (
            "Master of Science in Biohazardous Threat Agents and Emerging Infectious Diseases"
        ),
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "26.05",
        "delivery_format": "on_campus",
        "keywords": ["biohazardous threat agents and emerging infectious diseases"],
        "description": (
            "Focused study of dangerous pathogens, biodefense, and emerging infectious-disease "
            "threats covers the biology, surveillance, and policy of agents with public-health and "
            "national-security significance."
        ),
        "who_its_for": (
            "Students pursuing careers in biodefense, public health, or infectious-disease "
            "research and policy."
        ),
    },
    {
        "slug": "georgetown-health-informatics-ms",
        "school": "School of Medicine",
        "program_name": "Master of Science in Health Informatics and Data Science",
        "degree_type": "masters",
        "department": "Biomedical Graduate Education",
        "cip": "51.07",
        "delivery_format": "on_campus",
        "keywords": ["health informatics and data science"],
        "description": (
            "Training at the intersection of healthcare and computing covers electronic health "
            "records, clinical data analytics, and machine learning applied to biomedical and "
            "health-systems data."
        ),
        "who_its_for": (
            "Students bridging health care and data science for careers in clinical informatics "
            "and analytics."
        ),
    },
    {
        "slug": "georgetown-pharmacology-physiology-phd",
        "school": "School of Medicine",
        "program_name": "Doctor of Philosophy in Pharmacology and Physiology",
        "degree_type": "phd",
        "department": "Biomedical Graduate Education",
        "cip": "26.10",
        "delivery_format": "on_campus",
        "keywords": ["pharmacology and physiology"],
        "description": (
            "A research doctorate investigating how drugs and physiological systems govern health "
            "and disease combines coursework, laboratory rotations, and an original dissertation "
            "in molecular pharmacology or systems physiology."
        ),
        "who_its_for": (
            "Students committed to research careers studying drug action and the function of "
            "biological systems."
        ),
    },
    {
        "slug": "georgetown-biochemistry-mcb-phd",
        "school": "School of Medicine",
        "program_name": "Doctor of Philosophy in Biochemistry and Molecular and Cellular Biology",
        "degree_type": "phd",
        "department": "Biomedical Graduate Education",
        "cip": "26.02",
        "delivery_format": "on_campus",
        "keywords": ["biochemistry and molecular and cellular biology"],
        "description": (
            "A research doctorate probing the molecular and cellular foundations of life, from "
            "gene regulation and protein function to cell signaling, culminates in an original "
            "research dissertation."
        ),
        "who_its_for": (
            "Students pursuing independent research careers in the molecular and cellular life "
            "sciences."
        ),
    },
    {
        "slug": "georgetown-tumor-biology-phd",
        "school": "School of Medicine",
        "program_name": "Doctor of Philosophy in Tumor Biology",
        "degree_type": "phd",
        "department": "Biomedical Graduate Education",
        "cip": "26.02",
        "delivery_format": "on_campus",
        "keywords": ["tumor biology"],
        "description": (
            "A research doctorate dedicated to the molecular and cellular basis of cancer, "
            "including tumor genetics, the microenvironment, and therapeutics, is conducted within "
            "the Lombardi Comprehensive Cancer Center."
        ),
        "who_its_for": (
            "Students committed to independent cancer-research careers in academia or industry."
        ),
    },
    {
        "slug": "georgetown-microbiology-immunology-phd",
        "school": "School of Medicine",
        "program_name": "Doctor of Philosophy in Microbiology and Immunology",
        "degree_type": "phd",
        "department": "Biomedical Graduate Education",
        "cip": "26.05",
        "delivery_format": "on_campus",
        "keywords": ["microbiology and immunology"],
        "description": (
            "A research doctorate studying pathogens, host-pathogen interactions, and immune "
            "regulation trains students to investigate infectious disease and immunity through "
            "original laboratory research."
        ),
        "who_its_for": (
            "Students pursuing research careers in infectious disease, immunology, and microbial "
            "science."
        ),
    },
    {
        "slug": "georgetown-biostatistics-phd",
        "school": "School of Medicine",
        "program_name": "Doctor of Philosophy in Biostatistics",
        "degree_type": "phd",
        "department": "Biomedical Graduate Education",
        "cip": "26.11",
        "delivery_format": "on_campus",
        "keywords": ["biostatistics"],
        "description": (
            "A research doctorate developing advanced statistical theory and methods for "
            "biomedical research spans clinical trials, high-dimensional data, and the analysis of "
            "complex health datasets."
        ),
        "who_its_for": (
            "Quantitatively focused students aiming to develop statistical methodology for the "
            "health sciences."
        ),
    },
    {
        "slug": "georgetown-neuroscience-phd",
        "school": "School of Medicine",
        "program_name": "Doctor of Philosophy in Neuroscience",
        "degree_type": "phd",
        "department": "Interdisciplinary Program in Neuroscience",
        "cip": "26.15",
        "delivery_format": "on_campus",
        "keywords": ["neuroscience"],
        "description": (
            "An interdisciplinary research doctorate investigating the nervous system from "
            "molecules to behavior integrates cellular, systems, and cognitive neuroscience "
            "through coursework and an original dissertation."
        ),
        "who_its_for": (
            "Students committed to independent research careers across the breadth of neuroscience."
        ),
    },
]

REVIEWS = {
    "georgetown-mba-fulltime": {
        "summary": "Third-party coverage positions Georgetown McDonough's "
        "full-time MBA as a solid top-25 to top-30 program "
        "with a distinctive international and values-based "
        "identity, anchored by its signature Global Business "
        "Experience and a Washington, DC location prized for "
        "government, policy, and consulting access. Poets & "
        "Quants ranks it around #25 and notes employers rate "
        "its graduates highly, and the program recently "
        "rebooted its curriculum around AI, geopolitics, and "
        "analytics. Common cautions are its high cost and a "
        "relatively accessible acceptance rate with a median "
        "GMAT near 700, which sit below the most elite peer "
        "schools, along with a smaller full-time class.",
        "themes": [
            {
                "label": "International strength",
                "sentiment": "positive",
                "detail": "MBA deans rank McDonough among the top "
                "schools for international business, with a "
                "large share of recent classes coming from "
                "dozens of countries.",
            },
            {
                "label": "Global Business Experience",
                "sentiment": "positive",
                "detail": "Coverage repeatedly highlights the "
                "signature consulting-abroad capstone where "
                "students advise real international clients "
                "on-site.",
            },
            {
                "label": "DC location advantage",
                "sentiment": "positive",
                "detail": "The Washington, DC setting gives strong "
                "access to government, policy, consulting, "
                "and international-organization "
                "recruiting.",
            },
            {
                "label": "Curriculum reboot",
                "sentiment": "mixed",
                "detail": "A recent redesign around AI, geopolitics, "
                "and analytics is new and not yet proven, "
                "reflecting a program adapting to a tougher "
                "MBA job market.",
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": "Annual tuition around $70,000 makes total "
                "cost a frequently cited tradeoff for the "
                "program's ranking tier.",
            },
            {
                "label": "Selectivity vs. elite peers",
                "sentiment": "caution",
                "detail": "An acceptance rate near 64% and a median "
                "GMAT around 700 place it below top-10 "
                "programs in selectivity.",
            },
        ],
        "sources": [
            {
                "label": "Poets & Quants — Georgetown McDonough School Profile",
                "url": "https://poetsandquants.com/school-profile/georgetown-universitys-mcdonough-school-of-business/",
            },
            {
                "label": "Poets & Quants — Georgetown McDonough's MBA Just Got A Reboot",
                "url": "https://poetsandquants.com/2026/02/24/georgetown-mcdonoughs-mba-just-got-a-reboot/",
            },
            {
                "label": "Bloomberg Businessweek — Georgetown McDonough B-School Profile",
                "url": "https://www.bloomberg.com/business-schools/georgetown-mcdonough/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party "
        "sources; not individual verbatim reviews.",
    },
    "georgetown-jd": {
        "summary": "Georgetown Law is consistently described as a powerhouse for "
        "legal employment despite recent ranking turbulence: it fell to "
        "roughly #18 in the 2026 U.S. News Best Law Schools list, the "
        "largest drop among highly ranked schools, partly tied to its "
        "2022 decision to stop submitting internal data to U.S. News. "
        "Yet Above the Law ranks it 10th nationally for prestigious "
        "BigLaw outcomes, with about 54% of 2025 graduates landing Am "
        "Law 200 associate jobs. The dominant tradeoffs cited are its "
        "slipping U.S. News position relative to peers and the general "
        "caution that a law degree's payoff varies widely by graduate.",
        "themes": [
            {
                "label": "Elite employment outcomes",
                "sentiment": "positive",
                "detail": "Above the Law ranks Georgetown 10th for BigLaw "
                "placement, with roughly 54% of 2025 grads taking Am "
                "Law 200 associate roles.",
            },
            {
                "label": "DC / government access",
                "sentiment": "positive",
                "detail": "Its Washington, DC location is widely noted as an "
                "advantage for government, regulatory, and "
                "public-interest legal careers.",
            },
            {
                "label": "Scale and reputation",
                "sentiment": "positive",
                "detail": "Georgetown is one of the largest and most "
                "established law schools, retaining strong national "
                "brand recognition among employers.",
            },
            {
                "label": "U.S. News ranking decline",
                "sentiment": "caution",
                "detail": "It dropped to about #18 in the 2026 U.S. News "
                "rankings, the steepest fall among top schools.",
            },
            {
                "label": "Ranking-data transparency",
                "sentiment": "mixed",
                "detail": "Georgetown stopped submitting internal data to U.S. "
                "News in 2022, citing its Jesuit public-service "
                "values, which complicates ranking comparisons.",
            },
            {
                "label": "Variable return on a JD",
                "sentiment": "caution",
                "detail": "Georgetown's own research stresses that law-degree "
                "earnings vary enormously, so outcomes are not "
                "uniformly high even at strong schools.",
            },
        ],
        "sources": [
            {
                "label": "Above the Law — Best Law Schools For Getting A Biglaw Job (2026)",
                "url": "https://abovethelaw.com/2026/04/the-best-law-schools-for-getting-a-biglaw-job-2026/",
            },
            {
                "label": "The Hoya — GU Falls in Law School Rankings",
                "url": "https://thehoya.com/news/gu-falls-in-law-school-rankings/",
            },
            {
                "label": "U.S. News — Georgetown University Best Law Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/georgetown-university-03032",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources; "
        "not individual verbatim reviews.",
    },
    "georgetown-md": {
        "summary": "Coverage of Georgetown University School of Medicine emphasizes "
        "strong residency match results and a comparatively "
        "collaborative, mission-driven culture grounded in the Jesuit "
        "ideal of cura personalis, but notes that the school has "
        "withdrawn from U.S. News rankings, so a current ranked position "
        "is not published. Reporting on Match Day shows roughly 95% of "
        "graduating students matched into residencies, above the "
        "national figure, across two dozen specialties led by internal "
        "medicine and anesthesiology. Student-forum sentiment describes "
        "a less cutthroat environment helped by pass/fail preclinical "
        "grading, while common cautions are high cost of attendance and "
        "the school's choice to opt out of the U.S. News ranking system.",
        "themes": [
            {
                "label": "Strong match outcomes",
                "sentiment": "positive",
                "detail": "About 95% of graduates matched into residencies, "
                "exceeding the national average, across two dozen "
                "specialties.",
            },
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Student forums describe a less competitive "
                "environment supported by pass/fail preclinical "
                "grading.",
            },
            {
                "label": "Mission-driven identity",
                "sentiment": "positive",
                "detail": "The school's Jesuit cura personalis ethos and "
                "service orientation are recurring points in student "
                "and institutional discussion.",
            },
            {
                "label": "No U.S. News rank",
                "sentiment": "mixed",
                "detail": "Georgetown withdrew from U.S. News medical-school "
                "rankings, so there is no current published ranked "
                "position to compare.",
            },
            {
                "label": "Cost of attendance",
                "sentiment": "caution",
                "detail": "Forum discussions weighing Georgetown against state "
                "schools repeatedly flag its high tuition and total "
                "cost as a drawback.",
            },
        ],
        "sources": [
            {
                "label": "The Hoya — GU Medical School Match Rate Exceeds National Average",
                "url": "https://thehoya.com/news/gu-medical-school-match-rate-exceeds-national-average/",
            },
            {
                "label": "Student Doctor Network Forums — Georgetown (GUSOM) discussion",
                "url": "https://forums.studentdoctor.net/threads/maryland-umsom-vs-georgetown-gusom.1507587/",
            },
            {
                "label": "U.S. News — Georgetown University Best Medical Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/georgetown-university-04018",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources; "
        "not individual verbatim reviews.",
    },
    "georgetown-foreign-service-ms": {
        "summary": "Georgetown's MSFS is widely regarded as a "
        "premier graduate degree in international "
        "affairs: Foreign Policy magazine's 2024 survey "
        "of international-relations faculty, "
        "policymakers, and think-tank staff rated "
        "Georgetown's master's programs #1 in the world "
        "across all three groups, echoing earlier top "
        "finishes. Third-party and program sources "
        "describe it as one of the most selective "
        "international-relations programs anywhere, with "
        "deep history as the first graduate degree in "
        "international affairs and unmatched access to "
        "Washington's policy ecosystem. The most common "
        "cautions are its high cost and the practical "
        "reality that international-affairs careers, "
        "especially in government and the nonprofit "
        "sector, can offer modest early salaries "
        "relative to tuition.",
        "themes": [
            {
                "label": "Top-ranked in international affairs",
                "sentiment": "positive",
                "detail": "Foreign Policy's 2024 ranking placed "
                "Georgetown's IR master's programs "
                "first in the world across faculty, "
                "policymakers, and think-tank "
                "respondents.",
            },
            {
                "label": "Washington access",
                "sentiment": "positive",
                "detail": "Proximity to the State Department, "
                "agencies, think tanks, and "
                "international organizations is "
                "consistently cited as a core "
                "advantage.",
            },
            {
                "label": "Heritage and prestige",
                "sentiment": "positive",
                "detail": "SFS conferred the first graduate "
                "degree in international affairs in "
                "1922 and MSFS is described as among "
                "the most selective programs "
                "globally.",
            },
            {
                "label": "Selectivity",
                "sentiment": "mixed",
                "detail": "Its reputation as one of the most "
                "selective programs in the world "
                "makes admission highly competitive.",
            },
            {
                "label": "Cost vs. field salaries",
                "sentiment": "caution",
                "detail": "High tuition is a frequent tradeoff "
                "given that many foreign-service, "
                "government, and nonprofit career "
                "paths pay modestly early on.",
            },
        ],
        "sources": [
            {
                "label": "Georgetown SFS — Georgetown Ranks #1 in Foreign Policy 2024 Rankings",
                "url": "https://sfs.georgetown.edu/news/georgetown-ranks-1-in-foreign-policy-2024-rankings/",
            },
            {
                "label": "Georgetown SFS — Master of Science in Foreign Service",
                "url": "https://sfs.georgetown.edu/ms-foreign-service/",
            },
            {
                "label": "TopUniversities — Georgetown MSFS Program Profile",
                "url": "https://www.topuniversities.com/universities/georgetown-university/school-foreign-service/postgrad/master-science-foreign-service",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from public "
        "third-party sources; not individual verbatim "
        "reviews.",
    },
    "georgetown-public-policy-mpp": {
        "summary": "Georgetown McCourt's MPP is covered as a "
        "top-tier public-policy program that sits in the "
        "top tenth of U.S. public-affairs schools, with "
        "U.S. News rankings placing it around #10 to #12 "
        "overall and notably high in international policy "
        "and other specialties such as policy analysis "
        "and social policy. Its Washington, DC location "
        "and quantitative, analysis-heavy 48-credit "
        "curriculum are recurring strengths. Cautions "
        "surface mainly in student sentiment, where some "
        "reviewers cite uneven peer and career-support "
        "experiences relative to expectations, alongside "
        "the program's cost.",
        "themes": [
            {
                "label": "Top-tier U.S. News rank",
                "sentiment": "positive",
                "detail": "U.S. News has ranked McCourt around "
                "#10 to #12 overall in public affairs, "
                "in the top tenth of programs "
                "nationally.",
            },
            {
                "label": "International policy strength",
                "sentiment": "positive",
                "detail": "It ranks near the top in "
                "international policy and "
                "administration, with strong showings "
                "in policy analysis and social "
                "policy.",
            },
            {
                "label": "Analytical, DC-anchored curriculum",
                "sentiment": "positive",
                "detail": "The 48-credit MPP emphasizes "
                "quantitative policy analysis, "
                "leveraging its Washington, DC base "
                "for government and think-tank "
                "access.",
            },
            {
                "label": "Career and peer support",
                "sentiment": "caution",
                "detail": "Some student reviews report career "
                "and peer support feeling insufficient "
                "relative to comparable programs.",
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": "As with peer policy schools, tuition "
                "is a notable consideration given "
                "typical public-sector starting "
                "salaries.",
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Georgetown University Best Public Affairs Schools",
                "url": "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/georgetown-university-131496",
            },
            {
                "label": "Georgetown McCourt — McCourt School Rises in U.S. News Ranking",
                "url": "https://mccourt.georgetown.edu/news/mccourt-school-rises-in-us-news-world-report-ranking/",
            },
            {
                "label": "Niche — McCourt School of Public Policy Graduate Programs",
                "url": "https://www.niche.com/graduate-schools/mccourt-school-of-public-policy/",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from public "
        "third-party sources; not individual verbatim "
        "reviews.",
    },
    "georgetown-business-analytics-ms": {
        "summary": "Georgetown McDonough's MS in Business "
        "Analytics is covered as a highly ranked, "
        "fast-rising specialized master's: it placed "
        "2nd nationally in Fortune's Best Online "
        "Master's in Business Analytics ranking and "
        "around #12 in QS's business-analytics "
        "ranking, and the school recently expanded it "
        "to add a full-time, on-campus option. "
        "Reported outcomes are strong, with the Class "
        "of 2024 averaging about a $123,000 base "
        "salary, a roughly 30% salary increase, and "
        "most students changing jobs after "
        "graduation. Cautions are that much of the "
        "top-2 ranking pedigree is tied to the online "
        "format, dedicated independent student-review "
        "coverage for this specific program is thin, "
        "and tuition for a one-year specialized "
        "master's is high.",
        "themes": [
            {
                "label": "Top rankings",
                "sentiment": "positive",
                "detail": "Ranked 2nd in Fortune's Best "
                "Online Master's in Business "
                "Analytics and around #12 in QS's "
                "business-analytics ranking.",
            },
            {
                "label": "Strong salary outcomes",
                "sentiment": "positive",
                "detail": "The Class of 2024 reported an "
                "average base salary near $123,000 "
                "with about a 30% salary "
                "increase.",
            },
            {
                "label": "Career mobility",
                "sentiment": "positive",
                "detail": "Most of the cohort changed jobs "
                "after completing the program, "
                "indicating effective career "
                "pivots.",
            },
            {
                "label": "Program expansion",
                "sentiment": "mixed",
                "detail": "A newly added full-time on-campus "
                "option broadens access but is "
                "recent and less proven than the "
                "established format.",
            },
            {
                "label": "Ranking tied to online format",
                "sentiment": "caution",
                "detail": "The headline #2 ranking is "
                "specifically for the online "
                "program, so it may not fully "
                "translate to the on-campus "
                "experience.",
            },
            {
                "label": "Thin independent reviews and cost",
                "sentiment": "caution",
                "detail": "Dedicated student reviews for "
                "this specific program are sparse, "
                "and tuition for the specialized "
                "master's is high.",
            },
        ],
        "sources": [
            {
                "label": "Georgetown McDonough — MSBA Advances to Second in Fortune Ranking",
                "url": "https://msb.georgetown.edu/news-story/rankings/georgetown-m-s-in-business-analytics-advances-to-second-in-fortune-ranking/",
            },
            {
                "label": "Georgetown McDonough — Expands Top-Ranked MSBA with Full-Time Option",
                "url": "https://msb.georgetown.edu/news-story/curriculum/georgetown-mcdonough-expands-top-ranked-msba-program-with-full-time-on-campus-option/",
            },
            {
                "label": "GradReports — Georgetown University Reviews",
                "url": "https://www.gradreports.com/colleges/georgetown-university",
            },
        ],
        "disclaimer": "Aggregated and paraphrased from public "
        "third-party sources; not individual "
        "verbatim reviews.",
    },
}

# ── Derived per-slug indexes ───────────────────────────────────────────────
PROGRAMS: list[dict] = CATALOG
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}
_CIP_BY_SLUG: dict[str, str] = {p["slug"]: p["cip"] for p in PROGRAMS}
_WHO_BY_SLUG: dict[str, str] = {p["slug"]: p["who_its_for"] for p in PROGRAMS}
_REVIEWS_BY_SLUG: dict[str, dict] = REVIEWS

# Coverage-gated deep fields — genuinely sparse, recorded honestly as omitted per node
# (the gold reference is sparse on these too); never fabricated.
_TRACKS_BY_SLUG: dict[str, list] = {}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {}

# Build-time self-check: every spec has a cip + who.
_missing_cip = [s for s in PROGRAM_SLUGS if s not in _CIP_BY_SLUG]
_missing_who = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
assert not _missing_cip, f"programs missing cip: {_missing_cip}"
assert not _missing_who, f"programs missing who_its_for: {_missing_who}"
# No duplicate rendered (program_name, degree_type) across the catalog.
_seen_names: set[tuple] = set()
for _p in PROGRAMS:
    _key = (_p["program_name"], _p["degree_type"])
    assert _key not in _seen_names, f"duplicate program (name, degree): {_key}"
    _seen_names.add(_key)

# ── Cost / tuition ─────────────────────────────────────────────────────────
# Undergraduate sticker is one university-wide figure (2025-26), so it fills the entire
# bachelor's tier; graduate/professional schools bill per credit, so a verified flat or
# computed total is stamped where one is published and the rest are omit-with-reason.
_TUITION_UG = 71136  # 2025-26 published undergraduate tuition
_UNDERGRAD_COA = 96492  # 2025-26 first-year total cost of attendance
_AVG_NET_PRICE = 40815  # College Scorecard average net price
_UG_TUITION_SRC = (
    "Georgetown University — Fall 2025-Spring 2026 Undergraduate Tuition",
    "https://www.georgetown.edu/news/announcing-fall-2025-spring-2026-undergraduate-tuition-rates/",
)

# Programs with a verified flat or published-rate-times-published-credits total.
_LAW_JD_SRC = (
    "Georgetown Law — Tuition & Cost of Attendance 2025-26",
    "https://www.law.georgetown.edu/admissions-aid/financial-aid/tuition-cost-of-attendance/",
)
_MED_MD_SRC = (
    "Georgetown School of Medicine — Cost of Attendance 2025-26",
    "https://meded.georgetown.edu/admissions/financial-aid/costofattendance/",
)
_MBA_SRC = (
    "Georgetown McDonough — Full-time MBA Admissions & Tuition 2025-26",
    "https://msb.georgetown.edu/full-time-mba/admissions-tuition/",
)
_LLM_SRC = (
    "Georgetown Law — Tuition & Cost of Attendance 2025-26 (full-time LL.M.)",
    "https://www.law.georgetown.edu/admissions-aid/financial-aid/tuition-cost-of-attendance/",
)
_MCCOURT_SRC = (
    "Georgetown finaid — 2025-26 Graduate Program Cost of Attendance (McCourt $2,550/credit)",
    "https://finaid.georgetown.edu/graduate/aid-by-program/2025-26-graduate-program-cost-of-attendance/",
)
_GSAS_SRC = (
    (
        "Georgetown finaid — 2025-26 Graduate Program Cost of Attendance (Graduate School "
        "$2,652/credit)"
    ),
    "https://finaid.georgetown.edu/graduate/aid-by-program/2025-26-graduate-program-cost-of-attendance/",
)

_LLM_FULLTIME = 86294  # 2025-26 flat full-time LL.M. tuition
_MCCOURT_PER_CREDIT = 2550

# Explicit per-program cost overrides (verified flat rate or published per-credit x
# published credit count). Everything not here and not a bachelor's is omit-with-reason.
_COST_BY_SLUG: dict[str, dict] = {
    "georgetown-jd": {
        "tuition_usd": 83576,
        "src": _LAW_JD_SRC,
        "year": "2025-26",
        "note": "Published 2025-26 Georgetown Law J.D. annual tuition.",
    },
    "georgetown-md": {
        "tuition_usd": 66778,
        "src": _MED_MD_SRC,
        "year": "2025-26",
        "note": "Published 2025-26 Georgetown School of Medicine M.D. annual tuition.",
    },
    "georgetown-mba-fulltime": {
        "tuition_usd": 70108,
        "src": _MBA_SRC,
        "year": "2025-26",
        "note": "Published 2025-26 Georgetown McDonough full-time MBA annual tuition.",
    },
    "georgetown-public-policy-mpp": {
        "tuition_usd": _MCCOURT_PER_CREDIT * 48,
        "src": _MCCOURT_SRC,
        "year": "2025-26",
        "note": "McCourt published 2025-26 rate $2,550/credit x 48 credits (MPP).",
    },
    "georgetown-international-development-policy-midp": {
        "tuition_usd": _MCCOURT_PER_CREDIT * 48,
        "src": _MCCOURT_SRC,
        "year": "2025-26",
        "note": "McCourt published 2025-26 rate $2,550/credit x 48 credits (MIDP).",
    },
    "georgetown-data-science-public-policy-ms": {
        "tuition_usd": _MCCOURT_PER_CREDIT * 39,
        "src": _MCCOURT_SRC,
        "year": "2025-26",
        "note": "McCourt published 2025-26 rate $2,550/credit x 39 credits (MS-DSPP).",
    },
    "georgetown-computer-science-ms": {
        "tuition_usd": 2652 * 30,
        "src": _GSAS_SRC,
        "year": "2025-26",
        "note": "Graduate School published 2025-26 rate $2,652/credit x 30 credits (10 courses).",
    },
    "georgetown-data-science-analytics-ms": {
        "tuition_usd": 2652 * 30,
        "src": _GSAS_SRC,
        "year": "2025-26",
        "note": "Graduate School published 2025-26 rate $2,652/credit x 30 credits.",
    },
}
# All full-time LL.M. specializations bill the flat full-time rate.
for _llm in [
    "georgetown-llm-taxation",
    "georgetown-llm-international-business",
    "georgetown-llm-national-security",
    "georgetown-llm-environmental-energy",
    "georgetown-llm-global-health",
    "georgetown-llm-international-legal-studies",
    "georgetown-llm-technology-law",
    "georgetown-llm-general",
]:
    _COST_BY_SLUG[_llm] = {
        "tuition_usd": _LLM_FULLTIME,
        "src": _LLM_SRC,
        "year": "2025-26",
        "note": "Published 2025-26 Georgetown Law flat full-time LL.M. tuition.",
    }

# ── Graduate / professional per-credit-billed programs (matcher budget signal) ──
# The graduate schools that bill per credit hour publish a verified per-credit rate; the
# matcher reads a single ``tuition`` scalar, so each program carries the published rate ×
# its published required credit count (the same convention as the McCourt and Graduate-
# School masters above — MPP = $2,550 × 48, CS-MS = $2,652 × 30). Programs whose required
# credit count is NOT cleanly published, and funded research doctorates, stay
# omit-with-reason (never the undergraduate sticker copied down).
_GSAS_PER_CREDIT = 2652  # Graduate School of Arts & Sciences (finaid 2025-26 COA)
_SFS_PER_CREDIT = 2758  # Walsh School of Foreign Service per-credit rate (program pages)
_BGE_PER_CREDIT = 2529  # Biomedical Graduate Education (finaid 2025-26 COA)
_BGE_BIOTECH_PER_CREDIT = 2539  # BGE Biotechnology rate (finaid 2025-26 COA)
_HEALTH_PER_CREDIT = 2652  # School of Health (finaid 2025-26 COA)
_LAW_GRAD_PER_CREDIT = 3596  # Georgetown Law part-time / non-JD graduate per-credit
_NURSING_ENTRY_PER_CREDIT = 1586  # School of Nursing Entry-to-Nursing (finaid 2025-26 COA)

_SFS_SRC = (
    "Georgetown Walsh School of Foreign Service — program admissions & tuition pages "
    "(cost per credit $2,758)",
    "https://sfs.georgetown.edu/ms-foreign-service/admissions-tuition/",
)
_BGE_SRC = (
    "Georgetown finaid — 2025-26 Graduate Program Cost of Attendance "
    "(Biomedical Graduate Education $2,529/credit; Biotechnology $2,539/credit)",
    "https://finaid.georgetown.edu/graduate/aid-by-program/2025-26-graduate-program-cost-of-attendance/",
)
_HEALTH_SRC = (
    "Georgetown finaid — 2025-26 Graduate Program Cost of Attendance "
    "(School of Health $2,652/credit)",
    "https://finaid.georgetown.edu/graduate/aid-by-program/2025-26-graduate-program-cost-of-attendance/",
)
_BUSINESS_SRC = (
    "Georgetown finaid — 2025-26 Graduate Program Cost of Attendance (McDonough per-credit rates)",
    "https://finaid.georgetown.edu/graduate/aid-by-program/2025-26-graduate-program-cost-of-attendance/",
)
_LAW_GRAD_SRC = (
    "Georgetown Law — Tuition & Fees Academic Year 2025-26 (part-time/graduate $3,596/credit)",
    "https://www.law.georgetown.edu/your-life-career/wp-content/uploads/sites/60/2025/04/Tuition-and-Fees-2025-2026.pdf",
)
_NURSING_SRC = (
    "Georgetown finaid — 2025-26 Graduate Program Cost of Attendance (School of Nursing)",
    "https://finaid.georgetown.edu/graduate/aid-by-program/2025-26-graduate-program-cost-of-attendance/",
)
_SCS_RATE_SRC = (
    "Georgetown Student Accounts — School of Continuing Studies tuition rates",
    "https://studentaccounts.georgetown.edu/tuition/scs/",
)


def _per_credit_cost(tuition: int, src: tuple[str, str], note: str) -> dict:
    return {"tuition_usd": tuition, "src": src, "year": "2025-26", "note": note}


# Walsh School of Foreign Service master's — $2,758/credit × published degree credits
# (EIA is the exception, billed at the $2,652 Graduate School rate over 30 credits).
_COST_BY_SLUG.update(
    {
        "georgetown-foreign-service-ms": _per_credit_cost(
            _SFS_PER_CREDIT * 48, _SFS_SRC, "SFS published $2,758/credit × 48-credit MSFS degree."
        ),
        "georgetown-global-human-development-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 48, _SFS_SRC, "SFS published $2,758/credit × 48-credit GHD degree."
        ),
        "georgetown-arab-studies-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 36, _SFS_SRC, "SFS published $2,758/credit × 36-credit MAAS degree."
        ),
        "georgetown-asian-studies-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 36, _SFS_SRC, "SFS published $2,758/credit × 36-credit MASIA degree."
        ),
        "georgetown-ceres-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 36, _SFS_SRC, "SFS published $2,758/credit × 36-credit MAERES degree."
        ),
        "georgetown-european-studies-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 42,
            _SFS_SRC,
            "SFS published $2,758/credit × 42-credit MA European Studies degree.",
        ),
        "georgetown-latin-american-studies-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 36, _SFS_SRC, "SFS published $2,758/credit × 36-credit MALAS degree."
        ),
        "georgetown-migration-refugees-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 36, _SFS_SRC, "SFS published $2,758/credit × 36-credit MIMR degree."
        ),
        "georgetown-security-studies-ma": _per_credit_cost(
            _SFS_PER_CREDIT * 36, _SFS_SRC, "SFS published $2,758/credit × 36-credit SSP degree."
        ),
        "georgetown-environment-international-affairs-ms": _per_credit_cost(
            _GSAS_PER_CREDIT * 30,
            (
                "Georgetown Environment & International Affairs — Tuition & Financial Aid "
                "($2,652/credit × 30 credits)",
                "https://eia.georgetown.edu/admissions/tuition-financial-aid-2/",
            ),
            "Published Graduate School $2,652/credit × 30-credit EIA degree.",
        ),
    }
)

# Graduate School of Arts & Sciences academic master's — $2,652/credit × published credits.
# Programs whose total required credits are not cleanly published (Arabic & Islamic Studies,
# English — coursework + thesis with no stated total, Spanish Linguistics) stay omit-with-reason.
_COST_BY_SLUG.update(
    {
        "georgetown-american-government-ma": _per_credit_cost(
            _GSAS_PER_CREDIT * 30, _GSAS_SRC, "Graduate School $2,652/credit × 30-credit MA."
        ),
        "georgetown-applied-economics-ma": _per_credit_cost(
            _GSAS_PER_CREDIT * 30, _GSAS_SRC, "Graduate School $2,652/credit × 30-credit MA."
        ),
        "georgetown-cct-ma": _per_credit_cost(
            _GSAS_PER_CREDIT * 36, _GSAS_SRC, "Graduate School $2,652/credit × 36-credit CCT MA."
        ),
        "georgetown-conflict-resolution-ma": _per_credit_cost(
            _GSAS_PER_CREDIT * 34, _GSAS_SRC, "Graduate School $2,652/credit × 34-credit MA."
        ),
        "georgetown-german-ma": _per_credit_cost(
            _GSAS_PER_CREDIT * 36, _GSAS_SRC, "Graduate School $2,652/credit × 36-credit MA."
        ),
        "georgetown-history-ma": _per_credit_cost(
            _GSAS_PER_CREDIT * 30, _GSAS_SRC, "Graduate School $2,652/credit × 30-credit MAGIC MA."
        ),
        "georgetown-linguistics-ms": _per_credit_cost(
            _GSAS_PER_CREDIT * 36, _GSAS_SRC, "Graduate School $2,652/credit × 36-credit MS."
        ),
        "georgetown-mathematics-statistics-ms": _per_credit_cost(
            _GSAS_PER_CREDIT * 30, _GSAS_SRC, "Graduate School $2,652/credit × 30-credit MS."
        ),
        "georgetown-physics-ms": _per_credit_cost(
            _GSAS_PER_CREDIT * 31, _GSAS_SRC, "Graduate School $2,652/credit × 31-credit MS."
        ),
        "georgetown-spanish-literature-ms": _per_credit_cost(
            _GSAS_PER_CREDIT * 33, _GSAS_SRC, "Graduate School $2,652/credit × 33-credit MS."
        ),
    }
)

# McDonough School of Business master's — finaid 2025-26 per-credit rates × published credits
# (MSBA and MA International Business & Policy bill two year-specific rates).
_COST_BY_SLUG.update(
    {
        "georgetown-finance-ms": _per_credit_cost(
            2525 * 32, _BUSINESS_SRC, "McDonough MSF $2,525/credit × 32-credit degree."
        ),
        "georgetown-business-analytics-ms": _per_credit_cost(
            18 * 2332 + 12 * 2221,
            _BUSINESS_SRC,
            "McDonough MSBA: 18 credits @ $2,332 (yr 1) + 12 @ $2,221 (yr 2).",
        ),
        "georgetown-management-ms": _per_credit_cost(
            2106 * 30, _BUSINESS_SRC, "McDonough MiM $2,106/credit × 30-credit degree."
        ),
        "georgetown-international-business-policy-ma": _per_credit_cost(
            12 * 2728 + 18 * 2714,
            _BUSINESS_SRC,
            "McDonough MA-IBP: 12 credits @ $2,728 (yr 1) + 18 @ $2,714 (yr 2).",
        ),
        "georgetown-global-real-assets-ms": _per_credit_cost(
            2500 * 30, _BUSINESS_SRC, "McDonough Global Real Assets $2,500/credit × 30 credits."
        ),
        "georgetown-mba-flex": _per_credit_cost(
            2582 * 54, _BUSINESS_SRC, "McDonough Flex MBA $2,582/credit × 54-credit degree."
        ),
        "georgetown-environment-sustainability-management-ms": _per_credit_cost(
            _GSAS_PER_CREDIT * 30,
            (
                "Georgetown Environment & Sustainability Management — Admissions & Financing",
                "https://esm.georgetown.edu/admissions-financing/",
            ),
            "ESM billed at the Graduate School $2,652/credit × 30-credit degree.",
        ),
    }
)

# Georgetown Law non-JD graduate master's — $3,596/credit × published credits.
# The S.J.D. is billed on residency status (no single annual/total figure), so it is
# omit-with-reason rather than a stamped scalar.
_COST_BY_SLUG.update(
    {
        "georgetown-mlt": _per_credit_cost(
            _LAW_GRAD_PER_CREDIT * 24,
            _LAW_GRAD_SRC,
            "Georgetown Law $3,596/credit × 24-credit MLT.",
        ),
        "georgetown-msl-taxation": _per_credit_cost(
            _LAW_GRAD_PER_CREDIT * 24,
            _LAW_GRAD_SRC,
            "Georgetown Law $3,596/credit × 24 required credits (MSL Taxation).",
        ),
    }
)

# School of Continuing Studies — each program publishes a total program tuition (the rate ×
# its required credits, "reflects Fall semester of entry"). Standard on-campus MPS run
# $1,752/credit; online sections and Higher-Ed Administration run lower published rates;
# Urban & Regional Planning is 42 credits. Totals are the official program-page figures.
_SCS_PROGRAM_SRC = (
    "Georgetown SCS — program tuition & financial aid pages (published total program tuition)",
    "https://scs.georgetown.edu/admissions-aid/tuition-financial-aid/",
)
for _scs_slug, _scs_total, _scs_note in [
    ("georgetown-applied-intelligence-mps", 57816, "SCS published total (33 credits)."),
    ("georgetown-ai-management-mps", 52560, "SCS published total (30 credits)."),
    ("georgetown-cybersecurity-mps", 57816, "SCS published total (33 credits, on-campus)."),
    ("georgetown-design-management-mps", 55605, "SCS published total (33 credits, online rate)."),
    ("georgetown-emergency-disaster-management-mps", 57816, "SCS published total (33 credits)."),
    ("georgetown-human-resources-mps", 55605, "SCS published total (33 credits, online rate)."),
    ("georgetown-it-management-mps", 52560, "SCS published total (30 credits)."),
    ("georgetown-integrated-marketing-mps", 57816, "SCS published total (33 credits, on-campus)."),
    ("georgetown-journalism-mps", 52560, "SCS published total (30 credits)."),
    ("georgetown-project-management-mps", 52560, "SCS published total (30 credits)."),
    ("georgetown-public-relations-mps", 52560, "SCS published total (30 credits)."),
    ("georgetown-real-estate-mps", 57816, "SCS published total (33 credits)."),
    ("georgetown-sports-industry-mps", 52560, "SCS published total (30 credits)."),
    ("georgetown-supply-chain-mps", 57816, "SCS published total (33 credits)."),
    ("georgetown-liberal-studies-mals", 40380, "SCS published total program tuition (MALS)."),
]:
    _COST_BY_SLUG[_scs_slug] = {
        "tuition_usd": _scs_total,
        "src": _SCS_PROGRAM_SRC,
        "year": "2025-26",
        "note": _scs_note,
    }

# SCS programs with a verified program-specific rate / credit exception — cited to the
# program's own tuition page (spot-verified).
_COST_BY_SLUG["georgetown-higher-education-mps"] = {
    "tuition_usd": 40590,
    "src": (
        "Georgetown SCS — MPS Higher Education Administration, Tuition & Financial Aid",
        "https://scs.georgetown.edu/programs/448/master-of-professional-studies-in-higher-education-administration/tuition-financial-aid/",
    ),
    "year": "2025-26",
    "note": "SCS published total program tuition (33 credits at the reduced Higher-Ed rate).",
}
_COST_BY_SLUG["georgetown-urban-planning-mps"] = {
    "tuition_usd": 73584,
    "src": (
        "Georgetown SCS — MPS Urban & Regional Planning, Tuition & Financial Aid",
        "https://scs.georgetown.edu/programs/356/master-of-professional-studies-in-urban-regional-planning/tuition-financial-aid/",
    ),
    "year": "2025-26",
    "note": "SCS published total program tuition (42-credit degree).",
}
_COST_BY_SLUG["georgetown-global-sports-mps"] = {
    "tuition_usd": 76890,
    "src": (
        "Georgetown SCS — Executive MPS Global Sports Operations & Strategy, "
        "Tuition & Financial Aid",
        "https://scs.georgetown.edu/programs/559/hybrid/executive-masters-in-global-sports-operations-strategy/tuition-financial-aid/",
    ),
    "year": "2025-26",
    "note": "SCS published total program tuition (Executive rate; bundles two residencies).",
}
_COST_BY_SLUG["georgetown-liberal-studies-dls"] = {
    "tuition_usd": 65664,
    "src": (
        "Georgetown SCS — Doctor of Liberal Studies, Tuition & Financial Aid",
        "https://scs.georgetown.edu/programs/43/doctor-of-liberal-studies/tuition-financial-aid/",
    ),
    "year": "2025-26",
    "note": "SCS published total program tuition for the (non-funded) Doctor of Liberal Studies.",
}

# Biomedical Graduate Education (School of Medicine) master's — $2,529/credit (Biotechnology
# $2,539) × published required credits.
for _bge_slug, _bge_credits, _bge_rate in [
    ("georgetown-biochemistry-molecular-biology-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-biohazardous-threat-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-bioinformatics-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-biostatistics-ms", 32, _BGE_PER_CREDIT),
    ("georgetown-biotechnology-ms", 30, _BGE_BIOTECH_PER_CREDIT),
    ("georgetown-clinical-translational-research-ms", 33, _BGE_PER_CREDIT),
    ("georgetown-health-informatics-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-integrative-medicine-ms", 35, _BGE_PER_CREDIT),
    ("georgetown-integrative-neuroscience-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-microbiology-immunology-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-pharmacology-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-physiology-biophysics-ms", 30, _BGE_PER_CREDIT),
    ("georgetown-physiology-smp-ms", 31, _BGE_PER_CREDIT),
    ("georgetown-systems-medicine-ms", 32, _BGE_PER_CREDIT),
    ("georgetown-tumor-biology-ms", 30, _BGE_PER_CREDIT),
]:
    _COST_BY_SLUG[_bge_slug] = _per_credit_cost(
        _bge_rate * _bge_credits,
        _BGE_SRC,
        f"Biomedical Graduate Education ${_bge_rate:,}/credit × {_bge_credits}-credit MS.",
    )

# School of Health master's — $2,652/credit × published required credits.
for _h_slug, _h_credits in [
    ("georgetown-addiction-policy-practice-ms", 30),
    ("georgetown-climate-environment-health-ms", 30),
    ("georgetown-global-health-ms", 32),
    ("georgetown-global-infectious-disease-ms", 30),
    ("georgetown-health-systems-administration-ms", 42),
]:
    _COST_BY_SLUG[_h_slug] = _per_credit_cost(
        _HEALTH_PER_CREDIT * _h_credits,
        _HEALTH_SRC,
        f"School of Health $2,652/credit × {_h_credits}-credit MS.",
    )

# School of Nursing — the accelerated Entry-to-Nursing master's bills $1,586/credit over a
# verified 67-credit degree. The MSN proper varies by NP track (40-49 credits) with no single
# published 2025-26 per-credit figure, so it stays omit-with-reason below.
_COST_BY_SLUG["georgetown-nursing-entry-ms"] = _per_credit_cost(
    _NURSING_ENTRY_PER_CREDIT * 67,
    _NURSING_SRC,
    "School of Nursing $1,586/credit × 67-credit Entry-to-Nursing degree.",
)

# McCourt Master of Policy Management — McCourt published $2,550/credit × 36-credit degree.
_COST_BY_SLUG["georgetown-policy-management-mpm"] = {
    "tuition_usd": _MCCOURT_PER_CREDIT * 36,
    "src": (
        "Georgetown McCourt — Master of Policy Management Curriculum (36 credits) + McCourt "
        "published $2,550/credit rate",
        "https://mccourt.georgetown.edu/master-of-policy-management/curriculum/",
    ),
    "year": "2025-26",
    "note": "McCourt published $2,550/credit × 36-credit MPM degree.",
}
# Arabic & Islamic Studies MA — Graduate School $2,652/credit × 36 credits (AIS handbook).
_COST_BY_SLUG["georgetown-arabic-ma"] = {
    "tuition_usd": _GSAS_PER_CREDIT * 36,
    "src": (
        "Georgetown Arabic & Islamic Studies Graduate Handbook (M.A. — 36 credits) + Graduate "
        "School $2,652/credit",
        "https://sites.google.com/georgetown.edu/ais-graduate-handbook/m-a-in-arabic-and-islamic-studies",
    ),
    "year": "2025-26",
    "note": "Graduate School $2,652/credit × 36-credit MA in Arabic & Islamic Studies.",
}

# Programs whose tuition is honestly omitted, with the reason class.
_FUNDED_PHD_NOTE = (
    "Doctoral students at Georgetown are typically funded through fellowships, research, "
    "or teaching assistantships, with tuition waived for funded students; no flat annual "
    "sticker is stamped here rather than estimated."
)
_PER_CREDIT_NOTE = (
    "This graduate program is billed per credit hour rather than at a flat annual rate, "
    "and no verified single annual or total tuition figure is published, so it is omitted "
    "here rather than estimated. See the program's official cost page."
)

# ── Outcomes (institution-wide College Scorecard earnings on every program) ─
_OUTCOMES_CONDITIONS = (
    "Median earnings reflect Georgetown University graduates ten years after entry "
    "(U.S. Dept. of Education College Scorecard, institution-wide; not program-specific). "
    "Georgetown publishes no per-program employment rate or industry split, so those are omitted."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 103494,
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Georgetown, UNITID 131496)",
    "source_url": "https://collegescorecard.ed.gov/school/?131496",
}

# ── Application requirements ────────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Georgetown Application",
        "secondary-school transcript",
        "teacher and counselor recommendations",
        "Georgetown writing supplement",
        "standardized test scores (Georgetown requires SAT or ACT)",
    ],
    "deadlines": {"early_action": "November 1", "regular_decision": "January 10"},
    "source": "https://uadmissions.georgetown.edu/applying/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "online application",
        "bachelor's degree transcripts",
        "letters of recommendation",
        "statement of purpose / personal statement",
        "resume or CV",
    ],
    "deadlines": {"note": "Deadlines vary by program; see the program's official admissions page."},
    "source": "https://grad.georgetown.edu/admissions/",
}
_REQ_PROFESSIONAL = {
    "materials": [
        "professional-school application (e.g. LSAC / AMCAS where applicable)",
        "transcripts",
        "letters of recommendation",
        "personal statement",
        "resume",
    ],
    "deadlines": {"note": "Deadlines vary by program; see the school's official admissions page."},
    "source": "https://www.georgetown.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    if spec["degree_type"] == "professional":
        return dict(_REQ_PROFESSIONAL)
    return dict(_REQ_GRAD_GENERIC)


# Nominal full-time program length by credential (standard US nominal durations).
_DURATION_BY_DEGREE = {"bachelors": 48, "masters": 24, "phd": 60, "professional": 36}
_DURATION_OVERRIDE: dict[str, int] = {
    "georgetown-md": 48,
    "georgetown-mba-fulltime": 21,
    "georgetown-business-analytics-ms": 10,
    "georgetown-management-ms": 10,
    "georgetown-llm-taxation": 12,
    "georgetown-llm-international-business": 12,
    "georgetown-llm-national-security": 12,
    "georgetown-llm-environmental-energy": 12,
    "georgetown-llm-global-health": 12,
    "georgetown-llm-international-legal-studies": 12,
    "georgetown-llm-technology-law": 12,
    "georgetown-llm-general": 12,
}


def _duration_for(spec: dict) -> int:
    return _DURATION_OVERRIDE.get(spec["slug"], _DURATION_BY_DEGREE[spec["degree_type"]])


def _program_standard(slug: str, spec: dict) -> dict:
    omitted: list[str] = ["outcomes_data.employment_rate", "outcomes_data.top_industries"]
    if spec["degree_type"] != "bachelors" and slug not in _COST_BY_SLUG:
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


def _bachelor_cost() -> dict:
    return {
        "tuition_usd": _TUITION_UG,
        "total_cost_of_attendance": _UNDERGRAD_COA,
        "avg_net_price": _AVG_NET_PRICE,
        "breakdown": {"tuition": _TUITION_UG, "total_cost_of_attendance": _UNDERGRAD_COA},
        "funded": False,
        "note": (
            "Published 2025-26 Georgetown undergraduate tuition with the financial-aid "
            "office's total cost of attendance and the College Scorecard average net price. "
            "Georgetown meets demonstrated financial need, so many families pay less than sticker."
        ),
        "source": _UG_TUITION_SRC[0],
        "source_url": _UG_TUITION_SRC[1],
        "year": "2025-26",
    }


def _grad_cost(slug: str, spec: dict) -> dict:
    override = _COST_BY_SLUG.get(slug)
    if override is not None:
        return {
            "tuition_usd": override["tuition_usd"],
            "breakdown": {"tuition": override["tuition_usd"]},
            "funded": False,
            "note": override["note"],
            "source": override["src"][0],
            "source_url": override["src"][1],
            "year": override["year"],
        }
    # omit-with-reason: funded PhD, or per-credit-billed master's/professional
    funded = spec["degree_type"] == "phd"
    note = _FUNDED_PHD_NOTE if funded else _PER_CREDIT_NOTE
    return {
        "tuition_usd": None,
        "funded": funded,
        "note": note,
        "source": f"{spec['school']} — official program cost page",
        "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.georgetown.edu/"),
    }


def _lead_campus_photo(school_outcomes: dict) -> str | None:
    photos = school_outcomes.get("campus_photos") or []
    if photos and isinstance(photos[0], dict):
        return photos[0].get("url")
    return None


# ── Apply ───────────────────────────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Georgetown to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Georgetown is absent — safe on fresh/CI databases.
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
    inst.founded_year = 1789
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.georgetown.edu"
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
        about = dict(_ABOUT_DETAIL.get(spec["name"], {}))
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
        p.duration_months = _duration_for(spec)
        p.description_text = spec["description"]
        p.website_url = _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec["delivery_format"]
        p.content_sources = _program_content(spec["school"], spec["keywords"])
        if spec["degree_type"] == "bachelors":
            cost = _bachelor_cost()
        else:
            cost = _grad_cost(slug, spec)
        p.tuition = cost.get("tuition_usd")
        p.cost_data = cost
        p.cip_code = _CIP_BY_SLUG.get(slug)
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.who_its_for = _WHO_BY_SLUG.get(slug)
        p.highlights = None
        p.application_deadline = date(2027, 1, 10) if spec["degree_type"] == "bachelors" else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
