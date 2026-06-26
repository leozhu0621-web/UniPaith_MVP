"""Emory University — gold-standard profile data (institution + schools + program catalog).

Every value below is verified against an authoritative source (Emory's official pages, the
U.S. Dept. of Education College Scorecard / NCES for UNITID 139658, the Common Data Set,
and ranking bodies) and carries a citation, or is honestly omitted (recorded in that
node's ``_standard.omitted``) — never guessed.

The institution-level federal seed already wrote admit_rate, avg_net_price,
median_earnings_10yr, completion_rate, location, ownership, and campus photos;
``apply`` shallow-merges the remaining required fields onto it.

Scope note (resumption clause, SKILL §"Scope & resumption"): Emory was a 5-stub
institution seed with 2 campus photos and a dead feed. This pass takes the INSTITUTION
fully to gold, expands the verified campus-photo gallery to four entries, wires working
Trumba events + News Center atom feeds, and replaces the stubs with a real, verified,
field-specific catalog of 46 programs across eight degree-granting schools.

Graduate-tier tuition (2026-06-23, emorygradtuition1): stamps published 2025-26
master's/professional rates from Emory Student Financial Services — Laney $73,200,
Goizueta MBA $76,900, Rollins MPH $43,264 / MSPH $50,186, Candler MDiv $27,500,
Law JD $69,510, Medicine MD $59,000 — never the $64,280 undergraduate sticker.
PhD rows remain funded-omit-with-reason. The full Laney graduate catalog and deeper
per-program review coverage are IN-FLIGHT for a future run — recorded honestly, never
padded.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Emory University"
ENRICHED_AT = "2026-06-20"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # Emory publishes a student-faculty ratio but no single current instructional-faculty
    # headcount could be verified from a citable official page this session.
    "school_outcomes.scale.faculty_count",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "SACSCOC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    "qs_world_university_rankings": {"rank": 180, "year": 2026},
    "times_higher_education": {"rank": 101, "year": 2026},
    "us_news_national": {"rank": 24, "year": 2026},
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.1065,
    "avg_net_price": 22585,
    "median_earnings_10yr": 80137,
    "graduation_rate_6yr": 0.9109,
    "retention_rate_first_year": 0.95,
    "financial_aid": {
        "pell_grant_rate": 0.19,
        "cost_of_attendance": 82804,
    },
    "demographics": {
        "white": 0.38,
        "asian": 0.18,
        "hispanic": 0.09,
        "black": 0.08,
        "two_or_more": 0.05,
        "international": 0.17,
        "unknown": 0.05,
    },
    "test_scores": {
        "sat_total_25_75": [1470, 1550],
        "act_25_75": [33, 35],
    },
    "location": {"lat": 33.79111, "lng": -84.32333},
    "campus_basics": {"location": "Atlanta, Georgia"},
    "scale": {
        "student_faculty_ratio": "9:1",
        "endowment_usd": 11000000000,
    },
    "employed_or_continuing_ed": 0.92,
    "top_employer_industries": [
        "Healthcare",
        "Finance and consulting",
        "Technology",
    ],
    "research": {
        "labs": [
            "Emory Vaccine Center",
            "Winship Cancer Institute",
            "Yerkes National Primate Research Center",
            "Emory Center for AIDS Research",
            "AI.Humanity Initiative",
        ],
        "areas": [
            "Infectious disease and global health",
            "Cancer biology and oncology",
            "Neuroscience",
            "Vaccine development",
            "Bioethics and health policy",
            "Artificial intelligence and society",
        ],
        "lab_links": {
            "Emory Vaccine Center": "https://www.emoryvaccinecenter.org/",
            "Winship Cancer Institute": "https://winshipcancer.emory.edu/",
            "Yerkes National Primate Research Center": "https://www.yerkes.emory.edu/",
            "Emory Center for AIDS Research": "https://cfar.emory.edu/",
            "AI.Humanity Initiative": "https://aihumanity.emory.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division III (University Athletic Association)",
        "mascot": "Emory Eagles",
        "housing": "Residential campus with first-year and upperclass housing",
        "resources": [
            {"label": "Emory Athletics", "url": "https://emoryathletics.com/"},
            {"label": "Emory Libraries", "url": "https://libraries.emory.edu/"},
            {"label": "Michael C. Carlos Museum", "url": "https://carlos.emory.edu/"},
            {"label": "Schwartz Center for Performing Arts", "url": "https://schwartz.emory.edu/"},
            {"label": "Career Center", "url": "https://career.emory.edu/"},
        ],
    },
    "flagship": {
        "enrollment_total": 15912,
        "applicants": 33459,
        "admits": 3562,
        "admissions_cycle": "Class of 2029 (entering fall 2025; Emory Undergraduate Admission)",
        "founded_year": 1836,
    },
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/d/d1/Candler_Library%2C_Emory_University%2C_Night.jpg",
            "credit": "Wikimedia Commons / Alexanderfernbank (CC BY-SA 3.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Emory_University_in_Atlanta_Georgia_-_Aerial_View_%2853839381683%29.jpg/1920px-Emory_University_in_Atlanta_Georgia_-_Aerial_View_%2853839381683%29.jpg",
            "credit": "Wikimedia Commons / Tony Webster (CC BY 2.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Emory_University_Quad%2C_Atlanta%2C_GA_%28cropped%29.jpg/1920px-Emory_University_Quad%2C_Atlanta%2C_GA_%28cropped%29.jpg",
            "credit": "Wikimedia Commons / Keizers (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Michael_C._Carlos_Museum%2C_Emory_University%2C_Atlanta%2C_GA.jpg/1920px-Michael_C._Carlos_Museum%2C_Emory_University%2C_Atlanta%2C_GA.jpg",
            "credit": "Wikimedia Commons / Keizers (CC BY-SA 4.0)",
        },
    ],
    "media_credit": "Wikimedia Commons / Alexanderfernbank (CC BY-SA 3.0)",
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Emory, UNITID 139658)",
            "url": "https://collegescorecard.ed.gov/school/?139658",
        },
        {
            "label": "NCES College Navigator — Emory University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=139658",
        },
        {
            "label": "Emory Office of Institutional Data — Common Data Set",
            "url": "https://oir.emory.edu/home/institutional-data-and-research/common-data-set.html",
        },
        {
            "label": "Emory Undergraduate Admission — Class Profile",
            "url": "https://apply.emory.edu/discover/statistics/index.html",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Emory University (#24 National Universities)",
            "url": "https://www.usnews.com/best-colleges/emory-university-1564",
        },
        {
            "label": "QS World University Rankings 2026 — Emory University",
            "url": "https://www.topuniversities.com/universities/emory-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Emory University",
            "url": "https://www.timeshighereducation.com/world-university-rankings/emory-university",
        },
    ],
}

UNDERGRAD_COUNT = 7298

DESCRIPTION = (
    "Emory University is a private research university in Atlanta, Georgia, founded in "
    "1836 and chartered as Emory College in 1837. It enrolls about 7,300 undergraduates "
    "and some 8,600 graduate and professional students — roughly 15,900 in all — with a "
    "9:1 student-faculty ratio on a residential campus in the Druid Hills neighborhood, "
    "adjacent to the Centers for Disease Control and Prevention.\n\n"
    "Emory is organized into Emory College of Arts and Sciences, Oxford College (a "
    "two-year liberal-arts entry point), Goizueta Business School, the Nell Hodgson "
    "Woodruff School of Nursing, Rollins School of Public Health, Candler School of "
    "Theology, Emory School of Law, Emory School of Medicine, and the Laney Graduate "
    "School. Its research is anchored by the Emory Vaccine Center, Winship Cancer "
    "Institute, Yerkes National Primate Research Center, and the AI.Humanity initiative.\n\n"
    "A Carnegie R1 university accredited by SACSCOC and a member of the Association of "
    "American Universities, Emory ranks No. 24 among national universities by U.S. News, "
    "No. 101 in the world by Times Higher Education, and No. 180 by QS. It admitted about "
    "11% of first-year applicants for the Class of 2029 and holds an endowment of about "
    "$11 billion.\n\n"
    "Emory meets demonstrated financial need for admitted undergraduates: the average net "
    "price is about $22,600 a year against a published cost of attendance near $83,000, "
    "and graduates report strong placement in healthcare, finance and consulting, and "
    "technology. The Emory Eagles compete in NCAA Division III in the University Athletic "
    "Association."
)


_COLLEGE = "Emory College of Arts and Sciences"
_OXFORD = "Oxford College"
_GOIZUETA = "Goizueta Business School"
_NURSING = "Nell Hodgson Woodruff School of Nursing"
_ROLLINS = "Rollins School of Public Health"
_CANDLER = "Candler School of Theology"
_LAW = "Emory School of Law"
_MED = "Emory School of Medicine"
_LANEY = "Laney Graduate School"

_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://college.emory.edu/",
    _OXFORD: "https://oxford.emory.edu/",
    _GOIZUETA: "https://goizueta.emory.edu/",
    _NURSING: "https://nursing.emory.edu/",
    _ROLLINS: "https://sph.emory.edu/",
    _CANDLER: "https://candler.emory.edu/",
    _LAW: "https://law.emory.edu/",
    _MED: "https://med.emory.edu/",
    _LANEY: "https://www.gs.emory.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _COLLEGE, "sort_order": 1, "description": (
        "Emory College of Arts and Sciences is the undergraduate liberal-arts core on the "
        "Atlanta campus, offering more than seventy majors and minors across the humanities, "
        "natural sciences, and social sciences."
    )},
    {"name": _OXFORD, "sort_order": 2, "description": (
        "Oxford College is Emory's two-year liberal-arts college in Oxford, Georgia, where "
        "students complete their first two years before continuing to Emory College in Atlanta."
    )},
    {"name": _GOIZUETA, "sort_order": 3, "description": (
        "Goizueta Business School awards the BBA and a full-time MBA, known for healthcare "
        "and consulting placement in Atlanta."
    )},
    {"name": _NURSING, "sort_order": 4, "description": (
        "The Nell Hodgson Woodruff School of Nursing awards the BSN and graduate nursing "
        "degrees with clinical training through Emory Healthcare."
    )},
    {"name": _ROLLINS, "sort_order": 5, "description": (
        "Rollins School of Public Health, adjacent to the CDC, awards MPH, MSPH, and doctoral "
        "degrees in epidemiology, biostatistics, and global health."
    )},
    {"name": _CANDLER, "sort_order": 6, "description": (
        "Candler School of Theology, affiliated with the United Methodist Church, prepares "
        "students for ministry and faith-based leadership through the MDiv and related degrees."
    )},
    {"name": _LAW, "sort_order": 7, "description": (
        "Emory School of Law awards the J.D. and graduate law degrees with strength in health "
        "law, international law, and public interest practice."
    )},
    {"name": _MED, "sort_order": 8, "description": (
        "Emory School of Medicine awards the M.D. and graduate biomedical degrees in partnership "
        "with Emory Healthcare and affiliated research centers."
    )},
    {"name": _LANEY, "sort_order": 9, "description": (
        "The Laney Graduate School oversees PhD and master's programs across the arts and "
        "sciences, public health, and nursing for Emory's graduate students."
    )},
]

_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {
        "founded": "1836 (Emory College chartered 1837)",
        "research_centers": [
            "Center for the Study of Human Health",
            "Emory Center for Digital Scholarship",
            "Institute for Developing Nations",
        ],
    },
    _OXFORD: {"founded": "1836 (original Emory campus in Oxford, Georgia)"},
    _GOIZUETA: {
        "founded": "1919 (named Goizueta in 1994)",
        "research_centers": ["Business & Society Institute", "Emory Center for Alternative Investments"],
    },
    _NURSING: {"founded": "1905"},
    _ROLLINS: {"founded": "1990", "research_centers": ["Emory Global Health Institute", "Rollins COVID-19 Response"]},
    _CANDLER: {"founded": "1914"},
    _LAW: {"founded": "1916", "research_centers": ["Barton Child Law and Policy Center", "Vulnerability and the Human Condition Initiative"]},
    _MED: {
        "founded": "1854 (medical school charter; joined Emory 1915)",
        "research_centers": ["Emory Vaccine Center", "Winship Cancer Institute", "Yerkes National Primate Research Center"],
    },
    _LANEY: {"founded": "Named Laney Graduate School in 2009"},
}

_ABOUT_OMITTED: dict[str, list[str]] = {
    _COLLEGE: ["about_detail.leadership", "about_detail.faculty"],
    _OXFORD: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"],
    _GOIZUETA: ["about_detail.leadership", "about_detail.faculty"],
    _NURSING: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"],
    _CANDLER: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"],
    _LAW: ["about_detail.leadership", "about_detail.faculty"],
    _MED: ["about_detail.leadership", "about_detail.faculty"],
    _LANEY: ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"],
    _ROLLINS: ["about_detail.leadership", "about_detail.faculty"],
}

# news.emory.edu/rss.xml returns HTTP 200 with zero items (verified 2026-06-20); the
# verified Trumba university events RSS feeds Updates (Rice/UF pattern), and the News
# Center academics atom feed supplements editorial coverage. Trumba iCal feeds Events.
_EMORY_EVENTS_RSS = "https://www.trumba.com/calendars/emory-events.rss"
_EMORY_EVENTS_ICS = {"url": "https://www.trumba.com/calendars/emory-events.ics", "type": "ical"}
_EMORY_NEWS_ATOM = "https://news.emory.edu/tags/category/academics/index_atom.xml"

_SOCIAL_EMORY = {
    "instagram": "https://www.instagram.com/emoryuniversity/",
    "linkedin": "https://www.linkedin.com/school/emory-university/",
    "x": "https://x.com/EmoryUniversity",
    "youtube": "https://www.youtube.com/user/EmoryUniversity",
    "facebook": "https://www.facebook.com/EmoryUniversity/",
}

_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _GOIZUETA: {
        "instagram": "https://www.instagram.com/goizueta/",
        "linkedin": "https://www.linkedin.com/school/goizueta-business-school/",
    },
    _ROLLINS: {
        "instagram": "https://www.instagram.com/rollinssph/",
        "linkedin": "https://www.linkedin.com/school/rollins-school-of-public-health/",
    },
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _COLLEGE: ["Emory College", "undergraduate", "arts and sciences"],
    _OXFORD: ["Oxford College", "Oxford campus"],
    _GOIZUETA: ["Goizueta", "business school", "MBA", "BBA"],
    _NURSING: ["Woodruff School of Nursing", "nursing"],
    _ROLLINS: ["Rollins", "public health", "SPH"],
    _CANDLER: ["Candler", "theology", "divinity"],
    _LAW: ["Emory Law", "law school"],
    _MED: ["School of Medicine", "Emory Medicine"],
    _LANEY: ["Laney Graduate", "graduate school", "PhD"],
}

_SCHOOL_NEWS_RSS: dict[str, str] = {
    _ROLLINS: "https://sph.emory.edu/rss.xml",
    _CANDLER: "https://candler.emory.edu/feed/",
}


def _school_content(name: str) -> dict:
    news = _SCHOOL_NEWS_RSS.get(name, _EMORY_EVENTS_RSS)
    return {
        "news_rss": news,
        "news_url": "https://news.emory.edu/",
        "news_curated": name not in _SCHOOL_NEWS_RSS,
        "events_feed": dict(_EMORY_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL_EMORY),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _EMORY_EVENTS_RSS,
    "news_url": "https://news.emory.edu/",
    "news_curated": True,
    "events_feed": dict(_EMORY_EVENTS_ICS),
    "social": _SOCIAL_EMORY,
}

_CATALOG: list[tuple] = [
    (
        "Anthropology", "Bachelor of Arts in Anthropology", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Anthropology", 48, ["anthropology"],
        "Emory's anthropology major examines human societies and cultures across archaeology, biological anthropology, and sociocultural anthropology, with field and laboratory research in Atlanta and abroad.",
    ),
    (
        "Art History", "Bachelor of Arts in Art History", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Art History", 48, ["art history"],
        "The art history major studies visual culture from antiquity to the present, drawing on the Michael C. Carlos Museum collections for object-based study of painting, sculpture, and global art traditions.",
    ),
    (
        "Biology", "Bachelor of Science in Biology", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Biology", 48, ["biology"],
        "Biology at Emory spans molecular, cellular, organismal, and ecological scales, with undergraduate research pathways in genetics, neuroscience, and infectious disease on the Atlanta campus.",
    ),
    (
        "Biophysics", "Bachelor of Science in Biophysics", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Physics", 48, ["biophysics"],
        "The biophysics major integrates physics, chemistry, and biology to study living systems at molecular and cellular scales, preparing students for research in quantitative life sciences.",
    ),
    (
        "Chemistry", "Bachelor of Science in Chemistry", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Chemistry", 48, ["chemistry"],
        "Chemistry covers organic, inorganic, physical, and biological chemistry with core laboratory work and undergraduate research in Emory's chemistry department.",
    ),
    (
        "Classics", "Bachelor of Arts in Classics", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Classics", 48, ["classics"],
        "Classics combines Greek and Latin language study with the history, literature, and archaeology of the ancient Mediterranean world.",
    ),
    (
        "Comparative Literature", "Bachelor of Arts in Comparative Literature", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Comparative Literature", 48, ["comparative literature"],
        "Comparative literature studies literature across languages and cultures, examining translation, literary theory, and global literary traditions.",
    ),
    (
        "Computer Science", "Bachelor of Science in Computer Science", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Computer Science", 48, ["computer science"],
        "Emory's computer science major spans algorithms, systems, artificial intelligence, and human-computer interaction, with research ties to the Emory AI.Humanity initiative.",
    ),
    (
        "Data Science", "Bachelor of Science in Data Science", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Data and Decision Sciences", 48, ["data science"],
        "The data science major integrates statistics, machine learning, and domain coursework across the natural and social sciences through interdisciplinary tracks in the Data and Decision Sciences department.",
    ),
    (
        "Economics", "Bachelor of Arts in Economics", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Economics", 48, ["economics"],
        "Economics at Emory grounds students in microeconomic and macroeconomic theory and econometrics, with applied fields from health economics to development and public policy.",
    ),
    (
        "English", "Bachelor of Arts in English", "bachelors", 'Emory College of Arts and Sciences',
        "Department of English", 48, ["English"],
        "The English major studies literature in English across periods and genres, with creative writing workshops and critical theory on the Atlanta campus.",
    ),
    (
        "Environmental Sciences", "Bachelor of Science in Environmental Sciences", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Environmental Sciences", 48, ["environmental sciences"],
        "Environmental sciences links ecology, earth science, and policy to address sustainability, conservation, and climate change in urban and global contexts.",
    ),
    (
        "Film and Media", "Bachelor of Arts in Film and Media", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Film and Media", 48, ["film", "media"],
        "Film and media pairs critical study of cinema and media culture with production in film, video, and digital media.",
    ),
    (
        "History", "Bachelor of Arts in History", "bachelors", 'Emory College of Arts and Sciences',
        "Department of History", 48, ["history"],
        "History at Emory spans the Americas, Europe, Africa, Asia, and the Middle East, training students in archival research across premodern and modern periods.",
    ),
    (
        "Human Health", "Bachelor of Arts in Human Health", "bachelors", 'Emory College of Arts and Sciences',
        "Center for the Study of Human Health", 48, ["human health"],
        "Human health is an interdisciplinary major integrating biology, ethics, and social science to study health, disease, and well-being across the lifespan.",
    ),
    (
        "International Studies", "Bachelor of Arts in International Studies", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Political Science", 48, ["international studies"],
        "International studies examines global politics, economics, and culture, with language study and study-abroad pathways through Emory's Institute for Developing Nations.",
    ),
    (
        "Mathematics", "Bachelor of Science in Mathematics", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Mathematics", 48, ["mathematics"],
        "The mathematics major covers analysis, algebra, topology, and applied mathematics, with paths toward pure math, statistics, and computational work.",
    ),
    (
        "Music", "Bachelor of Arts in Music", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Music", 48, ["music"],
        "The music major combines performance, composition, theory, and ethnomusicology, with ensembles and recitals in the Schwartz Center for Performing Arts.",
    ),
    (
        "Neuroscience and Behavioral Biology", "Bachelor of Science in Neuroscience and Behavioral Biology", "bachelors", 'Emory College of Arts and Sciences',
        "Program in Neuroscience and Behavioral Biology", 48, ["neuroscience"],
        "Neuroscience and behavioral biology studies the nervous system from molecules and cells to cognition and behavior, integrating biology, psychology, and chemistry.",
    ),
    (
        "Philosophy", "Bachelor of Arts in Philosophy", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Philosophy", 48, ["philosophy"],
        "Philosophy covers logic, ethics, metaphysics, and the history of philosophy, with departmental strength in bioethics and the philosophy of mind.",
    ),
    (
        "Physics", "Bachelor of Science in Physics", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Physics", 48, ["physics"],
        "Physics spans classical and quantum mechanics, electromagnetism, and astrophysics, with undergraduate research in condensed matter and biophysics.",
    ),
    (
        "Political Science", "Bachelor of Arts in Political Science", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Political Science", 48, ["political science"],
        "Political science studies American politics, comparative politics, international relations, and political theory, with policy engagement in Atlanta.",
    ),
    (
        "Psychology", "Bachelor of Science in Psychology", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Psychology", 48, ["psychology"],
        "Psychology examines cognition, perception, social behavior, and clinical science, with laboratory research and ties to Emory's health sciences campus.",
    ),
    (
        "Public Policy Analysis", "Bachelor of Science in Public Policy Analysis", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Political Science", 48, ["public policy"],
        "Public policy analysis trains students in quantitative methods, economics, and political institutions to evaluate and design public programs.",
    ),
    (
        "Religion", "Bachelor of Arts in Religion", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Religion", 48, ["religion"],
        "The religion major studies the world's religious traditions — their texts, histories, and practices — across Asian, Abrahamic, and indigenous traditions.",
    ),
    (
        "Sociology", "Bachelor of Arts in Sociology", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Sociology", 48, ["sociology"],
        "Sociology examines social structure, inequality, institutions, and change, pairing social theory with quantitative and qualitative research methods.",
    ),
    (
        "Spanish", "Bachelor of Arts in Spanish", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Spanish and Portuguese", 48, ["Spanish"],
        "The Spanish major develops advanced language proficiency and studies the literatures and cultures of Spain and Latin America.",
    ),
    (
        "Theater Studies", "Bachelor of Arts in Theater Studies", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Theater Studies", 48, ["theater"],
        "Theater studies integrates acting, directing, design, and dramatic literature with production work in the Schwartz Center for Performing Arts.",
    ),
    (
        "African American Studies", "Bachelor of Arts in African American Studies", "bachelors", 'Emory College of Arts and Sciences',
        "Department of African American Studies", 48, ["African American studies"],
        "African American studies examines the histories, cultures, politics, and creative expression of African-descended peoples in the United States and the diaspora.",
    ),
    (
        "Linguistics", "Bachelor of Arts in Linguistics", "bachelors", 'Emory College of Arts and Sciences',
        "Department of Linguistics", 48, ["linguistics"],
        "Linguistics studies the structure of language — phonology, syntax, semantics, and sociolinguistics — and its cognitive and computational dimensions.",
    ),
    (
        "Business Administration", "Bachelor of Business Administration", "bachelors", 'Goizueta Business School',
        "Goizueta Business School", 48, ["BBA", "Goizueta"],
        "Goizueta's BBA is a four-year undergraduate business degree with concentrations in accounting, finance, marketing, and information systems, emphasizing analytical rigor and leadership in Atlanta.",
    ),
    (
        "Business Administration", "Master of Business Administration", "masters", 'Goizueta Business School',
        "Goizueta Business School", 24, ["MBA", "Goizueta"],
        "Goizueta's full-time MBA is a two-year general-management program in Atlanta known for small cohorts, strong healthcare and consulting placement, and ties to the city's business community.",
    ),
    (
        "Nursing", "Bachelor of Science in Nursing", "bachelors", 'Nell Hodgson Woodruff School of Nursing',
        "Nell Hodgson Woodruff School of Nursing", 48, ["nursing", "BSN"],
        "Emory's BSN prepares registered nurses through clinical training at Emory Healthcare and partner hospitals, with pathways in community health and acute care.",
    ),
    (
        "Public Health", "Master of Public Health", "masters", 'Rollins School of Public Health',
        "Rollins School of Public Health", 24, ["MPH", "Rollins", "public health"],
        "Rollins' MPH trains practitioners in epidemiology, biostatistics, and health policy, leveraging Emory's proximity to the CDC and global health partners in Atlanta.",
    ),
    (
        "Public Health", "Master of Science in Public Health", "masters", 'Rollins School of Public Health',
        "Rollins School of Public Health", 24, ["MSPH", "Rollins"],
        "The MSPH is a research-oriented public health master's emphasizing biostatistics, epidemiology, and environmental health sciences at Rollins.",
    ),
    (
        "Theology", "Master of Divinity", "masters", 'Candler School of Theology',
        "Candler School of Theology", 36, ["MDiv", "Candler", "theology"],
        "Candler's Master of Divinity prepares students for ordained ministry and faith-based leadership through biblical, theological, and pastoral formation in the Methodist tradition.",
    ),
    (
        "Law", "Juris Doctor", "professional", 'Emory School of Law',
        "Emory School of Law", 36, ["JD", "Emory Law"],
        "Emory Law awards the J.D. through a curriculum spanning constitutional law, international law, and health law, with clinics and externships in Atlanta.",
    ),
    (
        "Medicine", "Doctor of Medicine", "professional", 'Emory School of Medicine',
        "Emory School of Medicine", 48, ["MD", "Emory Medicine"],
        "Emory School of Medicine awards the M.D. through a curriculum integrating foundational science, early clinical experience, and research with Emory Healthcare and the CDC-adjacent Atlanta campus.",
    ),
    (
        "Biology", "Doctor of Philosophy in Biology", "phd", 'Laney Graduate School',
        "Department of Biology", 60, ["biology PhD", "Laney"],
        "The biology PhD supports doctoral research across molecular, cellular, and ecological biology in Emory's graduate division.",
    ),
    (
        "Computer Science", "Doctor of Philosophy in Computer Science", "phd", 'Laney Graduate School',
        "Department of Computer Science", 60, ["computer science PhD"],
        "The computer science PhD supports research in AI, systems, theory, and computational science with faculty in the Department of Computer Science.",
    ),
    (
        "Economics", "Doctor of Philosophy in Economics", "phd", 'Laney Graduate School',
        "Department of Economics", 60, ["economics PhD"],
        "The economics PhD trains researchers in microeconomics, macroeconomics, and econometrics, with applied strength in health and development economics.",
    ),
    (
        "Psychology", "Doctor of Philosophy in Psychology", "phd", 'Laney Graduate School',
        "Department of Psychology", 60, ["psychology PhD"],
        "The psychology PhD advances research in cognition, clinical science, and systems neuroscience using behavioral and neuroimaging methods.",
    ),
    (
        "Chemistry", "Doctor of Philosophy in Chemistry", "phd", 'Laney Graduate School',
        "Department of Chemistry", 60, ["chemistry PhD"],
        "The chemistry PhD trains researchers across synthetic, physical, biological, and materials chemistry in faculty laboratories.",
    ),
    (
        "History", "Doctor of Philosophy in History", "phd", 'Laney Graduate School',
        "Department of History", 60, ["history PhD"],
        "The history PhD supports doctoral research across American, European, African, and global history with archival training.",
    ),
    (
        "Biostatistics", "Doctor of Philosophy in Biostatistics", "phd", 'Laney Graduate School',
        "Department of Biostatistics and Bioinformatics", 60, ["biostatistics PhD", "Rollins"],
        "The biostatistics PhD, housed at Rollins, trains researchers in statistical methods for public health, clinical trials, and genomics.",
    ),
    (
        "Computer Science", "Master of Science in Computer Science", "masters", 'Laney Graduate School',
        "Department of Computer Science", 24, ["computer science MS"],
        "The MS in computer science offers advanced coursework and research preparation across core areas of computing at Emory.",
    ),
]

_SLUG_REPL = {"&": "and", " ": "-", "'": "", ".": "", ",": "", "(": "", ")": "", ":": ""}


def _slugify(text_value: str) -> str:
    s = text_value.lower()
    for k, v in _SLUG_REPL.items():
        s = s.replace(k, v)
    return "-".join(p for p in s.split("-") if p)


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for field, pname, dtype, school, dept, dur, kw, desc in _CATALOG:
        suffix = {"phd": "phd", "professional": "prof", "masters": "ms"}.get(
            dtype, "bs" if "Science" in pname else "ba"
        )
        if dtype == "bachelors" and "Business Administration" in pname:
            suffix = "bba"
        elif dtype == "masters" and "Public Health" in pname and "Science" in pname:
            suffix = "msph"
        elif dtype == "masters" and "Public Health" in pname:
            suffix = "mph"
        elif dtype == "masters" and "Divinity" in pname:
            suffix = "mdiv"
        elif dtype == "masters" and "Business Administration" in pname:
            suffix = "mba"
        elif dtype == "masters" and "Computer Science" in pname:
            suffix = "ms"
        slug = f"emory-{_slugify(field)}-{suffix}"
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
            "delivery_format": "in_person",
            "keywords": list(kw),
            "description": desc,
        })
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_FLAGSHIP = "emory-business-administration-mba"

_TUITION_UG = 64280
_UNDERGRAD_COA = 82804
_AVG_NET_PRICE = 22585
_COST_SRC = (
    "Emory Office of Financial Aid 2025-26 cost of attendance + College Scorecard (UNITID 139658)",
    "https://studentaid.emory.edu/undergraduate/cost/index.html",
)

_BURSAR_TUITION_SRC = (
    "Emory University Student Financial Services — 2025-2026 Tuition Rates",
    "https://studentfinancials.emory.edu/_includes/documents/tuition_rates_25-26.pdf",
)
_LAW_COA_SRC = (
    "Emory Student Financial Aid — Law (JD) cost of attendance 2025-26",
    "https://studentaid.emory.edu/_includes/documents/sections/graduate/apply/coa_law.pdf",
)

# ── Published graduate-tier tuition (REPAIR_BACKLOG #4 — master's/professional
# starvation behind a 100% bachelor's tier) ──────────────────────────────────
# Emory bills graduate/professional tuition BY SCHOOL on the Student Financial Services
# rate sheet (2025-26). Program.tuition is the matcher's ANNUAL budget input — stamp the
# published full-time sticker, never the $64,280 undergraduate rate copied down.
_LGS_SEM = 24400  # Laney Graduate School per term (fall/spring/summer)
_LGS_ANNUAL = _LGS_SEM * 3  # $73,200 across three terms
_GOIZUETA_MBA_SEM = 38450  # Traditional full-time MBA per term
_GOIZUETA_MBA_ANNUAL = _GOIZUETA_MBA_SEM * 2  # fall + spring academic year
_ROLLINS_MPH_SEM = 21632  # Traditional MPH (4-semester plan) per term
_ROLLINS_MPH_ANNUAL = _ROLLINS_MPH_SEM * 2
_ROLLINS_MSPH_SEM = 25093  # Traditional MSPH per term
_ROLLINS_MSPH_ANNUAL = _ROLLINS_MSPH_SEM * 2
_CANDLER_MDIV_SEM = 13750  # MDiv / MRL / MRPL / MTS / ThM per term
_CANDLER_MDIV_ANNUAL = _CANDLER_MDIV_SEM * 2  # $27,500 fall + spring
_LAW_JD_ANNUAL = 69510  # JD fixed annual tuition (12+ credits)
_MED_MD_SEM = 29500  # M.D. per fall/spring term (summer not billed)
_MED_MD_ANNUAL = _MED_MD_SEM * 2  # $59,000


def _annual_grad_cost(
    tuition_usd: int,
    *,
    note: str,
    source: str,
    source_url: str,
    year: str,
) -> dict:
    return {
        "tuition_usd": tuition_usd,
        "funded": False,
        "note": note,
        "source": source,
        "source_url": source_url,
        "year": year,
    }


_COST_BY_SLUG: dict[str, dict] = {
    "emory-business-administration-mba": _annual_grad_cost(
        _GOIZUETA_MBA_ANNUAL,
        note=(
            "Goizueta Traditional full-time MBA tuition: "
            f"${_GOIZUETA_MBA_SEM:,} per fall and spring term "
            f"(${_GOIZUETA_MBA_ANNUAL:,} academic-year tuition; summer terms "
            "bill at the same per-term rate when enrolled)."
        ),
        source=_BURSAR_TUITION_SRC[0],
        source_url=_BURSAR_TUITION_SRC[1],
        year="2025-26",
    ),
    "emory-public-health-mph": _annual_grad_cost(
        _ROLLINS_MPH_ANNUAL,
        note=(
            "Rollins Traditional MPH (four-semester plan): "
            f"${_ROLLINS_MPH_SEM:,} per fall and spring term "
            f"(${_ROLLINS_MPH_ANNUAL:,} academic-year tuition on the "
            "four-semester plan)."
        ),
        source=_BURSAR_TUITION_SRC[0],
        source_url=_BURSAR_TUITION_SRC[1],
        year="2025-26",
    ),
    "emory-public-health-msph": _annual_grad_cost(
        _ROLLINS_MSPH_ANNUAL,
        note=(
            "Rollins Traditional MSPH: "
            f"${_ROLLINS_MSPH_SEM:,} per fall and spring term "
            f"(${_ROLLINS_MSPH_ANNUAL:,} academic-year tuition on the "
            "four-semester plan)."
        ),
        source=_BURSAR_TUITION_SRC[0],
        source_url=_BURSAR_TUITION_SRC[1],
        year="2025-26",
    ),
    "emory-theology-mdiv": _annual_grad_cost(
        _CANDLER_MDIV_ANNUAL,
        note=(
            "Candler Master of Divinity: "
            f"${_CANDLER_MDIV_SEM:,} per fall and spring term "
            f"(${_CANDLER_MDIV_ANNUAL:,} academic-year tuition; MDiv is a "
            "three-year program)."
        ),
        source=_BURSAR_TUITION_SRC[0],
        source_url=_BURSAR_TUITION_SRC[1],
        year="2025-26",
    ),
    "emory-law-prof": _annual_grad_cost(
        _LAW_JD_ANNUAL,
        note=(
            "Emory Law J.D. fixed tuition for 12 or more credit hours per "
            f"academic year (${_LAW_JD_ANNUAL:,} fall 2025–spring 2026)."
        ),
        source=_LAW_COA_SRC[0],
        source_url=_LAW_COA_SRC[1],
        year="2025-26",
    ),
    "emory-medicine-prof": _annual_grad_cost(
        _MED_MD_ANNUAL,
        note=(
            "Emory School of Medicine M.D. tuition: "
            f"${_MED_MD_SEM:,} per fall and spring term "
            f"(${_MED_MD_ANNUAL:,} academic-year tuition; medical students are "
            "not assessed tuition in summer terms)."
        ),
        source=_BURSAR_TUITION_SRC[0],
        source_url=_BURSAR_TUITION_SRC[1],
        year="2025-26",
    ),
    "emory-computer-science-ms": _annual_grad_cost(
        _LGS_ANNUAL,
        note=(
            "Laney Graduate School full-time tuition: "
            f"${_LGS_SEM:,} per term across fall, spring, and summer "
            f"(${_LGS_ANNUAL:,} annual full-time rate)."
        ),
        source=_BURSAR_TUITION_SRC[0],
        source_url=_BURSAR_TUITION_SRC[1],
        year="2025-26",
    ),
}


def _published_grad_cost(spec: dict) -> dict | None:
    return None


def _grad_has_verified_tuition(spec: dict) -> bool:
    return spec["slug"] in _COST_BY_SLUG or _published_grad_cost(spec) is not None

_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after "
    "entry (U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 80137,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Emory, UNITID 139658)",
    "source_url": "https://collegescorecard.ed.gov/school/?139658",
}

_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or QuestBridge Application",
        "Emory writing supplement",
        "Secondary-school report + transcript",
        "Two teacher evaluations + counselor recommendation",
        "SAT or ACT scores (test-optional policy; verify current cycle on admissions site)",
    ],
    "deadlines": {
        "early_decision_i": "November 1",
        "early_decision_ii": "January 1",
        "regular_decision": "January 1",
    },
    "source": "https://apply.emory.edu/apply/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online application",
        "Transcripts from all prior institutions",
        "Letters of recommendation",
        "Statement of purpose",
        "Standardized/English-proficiency scores where required by the program",
    ],
    "deadlines": {
        "note": "Deadlines vary by program; see the program's official admissions page.",
    },
    "source": "https://www.gs.emory.edu/admissions/index.html",
}
_REQ_MBA = {
    "materials": [
        "Goizueta application + essays",
        "GMAT, GRE, or EA score",
        "Undergraduate transcripts",
        "Two recommendations",
        "Resume + interview",
    ],
    "deadlines": {
        "round_1": "October",
        "round_2": "January",
        "round_3": "March",
    },
    "source": "https://goizueta.emory.edu/full-time-mba/admissions",
}

_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "cohort_size": "About 180 students per entering full-time MBA class",
        "source": "Goizueta Business School — class profile",
        "source_url": "https://goizueta.emory.edu/full-time-mba/admissions/class-profile",
    },
}
_TRACKS_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {}

_REVIEWS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "summary": (
            "Reviewers describe Goizueta's full-time MBA as a strong regional program in "
            "Atlanta with notable healthcare and consulting placement, intimate cohort size, "
            "and solid faculty access. Common cautions are a smaller national brand than "
            "top-tier M7 programs and a recruiting footprint concentrated in the Southeast."
        ),
        "themes": [
            {
                "label": "Healthcare strength",
                "sentiment": "positive",
                "detail": (
                    "Proximity to the CDC, Emory Healthcare, and Atlanta's health sector "
                    "drives distinctive healthcare MBA pathways."
                ),
            },
            {
                "label": "Consulting placement",
                "sentiment": "positive",
                "detail": (
                    "Graduates place into management consulting, especially in the Southeast "
                    "and healthcare-adjacent consulting."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": (
                    "A relatively small class supports close faculty relationships and "
                    "collaborative culture."
                ),
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": (
                    "Goizueta ranks well regionally but carries less national prestige "
                    "than M7 peers for coast-to-coast recruiting."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — Goizueta Business School coverage",
                "url": "https://poetsandquants.com/school-profile/emory-university-goizueta-business-school/",
            },
            {
                "label": "U.S. News Best Business Schools 2026 — Emory (Goizueta)",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/emory-university-01058",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "emory-public-health-mph": {
        "summary": (
            "Coverage consistently places Rollins among the very top U.S. schools of public "
            "health — ranked No. 2 in the nation by peers in U.S. News & World Report's 2026 "
            "Best Public Health Schools list — with reviewers citing its Atlanta location "
            "beside the CDC, Emory Healthcare, and CARE, and depth in epidemiology, "
            "biostatistics, and global health. The most common caution is high cost and a "
            "competitive applicant pool relative to public-school MPH options."
        ),
        "themes": [
            {"label": "Top-ranked reputation", "sentiment": "positive", "detail": "Ranked No. 2 nationally among accredited schools of public health by U.S. News peers in 2026, for the second year running."},
            {"label": "CDC and Atlanta network", "sentiment": "positive", "detail": "Proximity to the CDC, The Carter Center, CARE, and Emory's health system drives practicum placements and applied research."},
            {"label": "Epi and biostatistics depth", "sentiment": "positive", "detail": "Reviewers single out strong epidemiology and biostatistics faculty and global-health pathways."},
            {"label": "Cost", "sentiment": "caution", "detail": "Private-school tuition makes the MPH expensive relative to in-state public programs; aid varies by department."},
        ],
        "sources": [
            {"label": "Rollins School of Public Health — ranked No. 2 by U.S. News 2026", "url": "https://sph.emory.edu/news/rollins-school-public-health-ranked-2-again-by-peers-us-news-world-report-2026"},
            {"label": "U.S. News — Best Health Schools, Emory (Rollins)", "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/emory-university-139658"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "emory-nursing-bs": {
        "summary": (
            "Emory's Nell Hodgson Woodruff School of Nursing draws strong third-party coverage: "
            "U.S. News & World Report ranked its BSN program No. 2 in the nation for 2026 (No. 1 "
            "in 2024), and the school sits among the top five in NIH nursing research funding and "
            "is an NLN Center of Excellence. Reviewers praise clinical immersion across Emory "
            "Healthcare; the main cautions are a small, highly selective cohort and an intensive, "
            "fast-paced clinical schedule."
        ),
        "themes": [
            {"label": "Top-ranked BSN", "sentiment": "positive", "detail": "U.S. News ranked the BSN No. 2 nationally in 2026 (No. 1 in 2024) — top five every year since the undergraduate rankings began."},
            {"label": "Clinical placement", "sentiment": "positive", "detail": "Clinical rotations across Emory Healthcare and partner Atlanta hospitals give early, hands-on patient experience."},
            {"label": "Research funding", "sentiment": "positive", "detail": "Among the top five U.S. nursing schools in NIH funding and a National League for Nursing Center of Excellence."},
            {"label": "Selective, intensive cohort", "sentiment": "caution", "detail": "A small BSN cohort (~340 students) and a demanding clinical schedule make admission and the workload competitive."},
        ],
        "sources": [
            {"label": "Emory News — BSN ranked No. 2 by U.S. News (2026)", "url": "https://news.emory.edu/stories/2025/09/son_us_news_undergrad_2026/story.html"},
            {"label": "U.S. News — Best Nursing Schools, Emory (Woodruff)", "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/emory-university-33063"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "emory-law-prof": {
        "summary": (
            "Coverage describes Emory Law as a solidly mid-first-tier school — ranked No. 38 by "
            "U.S. News & World Report for 2025 — with particular recognition in health law, "
            "transactional and business law, intellectual property, international and comparative "
            "law, and law and religion. Reviewers note a strong Atlanta market and clinics; the "
            "common cautions are a national profile below the T14 and a recruiting pull "
            "concentrated in the Southeast."
        ),
        "themes": [
            {"label": "Health law strength", "sentiment": "positive", "detail": "Emory's health care law program ranks in the U.S. News top 25 (around #23), reinforced by the Atlanta medical and CDC ecosystem."},
            {"label": "Transactional and IP focus", "sentiment": "positive", "detail": "Recognized strength in business/corporate law, contracts, intellectual property, and international and comparative law."},
            {"label": "Atlanta market and clinics", "sentiment": "positive", "detail": "Clinics, externships, and a major legal market in Atlanta support practical experience and regional placement."},
            {"label": "National profile", "sentiment": "caution", "detail": "Ranked in the mid-first tier (around #38), with strongest hiring in the Southeast rather than coast-to-coast."},
        ],
        "sources": [
            {"label": "U.S. News — Best Law Schools, Emory University", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/emory-university-03039"},
            {"label": "Emory Law — message from the dean on rankings", "url": "https://law.emory.edu/news-and-events/releases/2024/04/message-dean-ranking-2024-2025.html"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "emory-medicine-prof": {
        "summary": (
            "Third-party coverage rates Emory School of Medicine a top research medical school — "
            "U.S. News places it in Tier 1 for research (a lower tier for primary care) — with "
            "noted strength in infectious disease and vaccines, organ transplantation, oncology "
            "through the Winship Cancer Institute, and global health. Reviewers highlight the "
            "five-month third-year 'Discovery' research phase; the main caution is that the "
            "program's profile is research-led rather than primary-care-led."
        ),
        "themes": [
            {"label": "Research tier", "sentiment": "positive", "detail": "Ranked in U.S. News's top (Tier 1) research band, with robust NIH funding across basic, translational, and clinical science."},
            {"label": "Infectious disease and vaccines", "sentiment": "positive", "detail": "Distinctive strength in infectious disease, HIV/AIDS, and vaccine science (Emory Vaccine Center), aided by CDC proximity."},
            {"label": "Discovery research phase", "sentiment": "positive", "detail": "A dedicated five-month third-year 'Discovery' phase lets students pursue research or scholarly projects."},
            {"label": "Primary-care emphasis", "sentiment": "caution", "detail": "The school ranks notably higher for research than for primary care, so a primary-care-focused applicant should weigh fit."},
        ],
        "sources": [
            {"label": "U.S. News — Best Medical Schools, Emory University", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/emory-university-04023"},
            {"label": "Emory Woodruff Health Sciences Center — rankings", "url": "https://whsc.emory.edu/about/facts-figures/rankings.html"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
    "emory-business-administration-bba": {
        "summary": (
            "Goizueta's undergraduate BBA earns strong coverage — ranked among the top 10 "
            "nationally by Poets&Quants and No. 12 by U.S. News & World Report — with reviewers "
            "citing high selectivity (about a 10% admit rate), excellent placement (98% of the "
            "Class of 2025 with offers within three months, ~$87,749 average salary), a recently "
            "redesigned tech- and analytics-heavy curriculum, and full STEM designation. The most "
            "cited caution is a comparatively lower alumni-rated academic-experience score."
        ),
        "themes": [
            {"label": "Top-10 BBA ranking", "sentiment": "positive", "detail": "Ranked in the Poets&Quants top 10 (8th in 2025) and No. 12 by U.S. News — in the top 15 for undergraduate business for over 15 years."},
            {"label": "Career outcomes", "sentiment": "positive", "detail": "98% of 2025 BBA grads received offers within three months at an average salary near $87,749, with strong consulting, finance, and healthcare placement."},
            {"label": "STEM-designated, redesigned curriculum", "sentiment": "positive", "detail": "A 2023 curriculum overhaul added data analytics, technology, and experiential learning, and the program is now fully STEM-designated."},
            {"label": "Academic-experience rating", "sentiment": "caution", "detail": "Goizueta ranks lower on the alumni-surveyed academic-experience measure (around #28) than on selectivity and outcomes."},
        ],
        "sources": [
            {"label": "Poets&Quants for Undergrads — Emory (Goizueta) profile", "url": "https://poetsandquantsforundergrads.com/school-profile/emory-university-goizueta-business-school/"},
            {"label": "EmoryBusiness — BBA No. 12 by U.S. News (2025)", "url": "https://www.emorybusiness.com/2025/09/23/bba-program-rises-to-12th-in-nation-by-u-s-news-world-report/"},
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
}


# ── Matcher-core CIP join key (REPAIR_BACKLOG #1) ─────────────────────────────
# ``cip_code`` is the CIP code the CPEF matcher uses to resolve a program's field to
# ``ref_majors`` + the field-66 vocabulary (the interest/field signal alongside the
# ``description_text`` embedding). Emory's catalog shipped ``cip_code`` null fleet-wide,
# so those programs scored field-blind. Each code is the standard IPEDS CIP-2020 code for
# the program's field — a published taxonomy lookup, never a guess.
_CIP_BY_SLUG: dict[str, str] = {
    "emory-anthropology-ba": "45.0201",
    "emory-art-history-ba": "50.0703",
    "emory-biology-bs": "26.0101",
    "emory-biophysics-bs": "26.0203",
    "emory-chemistry-bs": "40.0501",
    "emory-classics-ba": "16.1200",
    "emory-comparative-literature-ba": "16.0104",
    "emory-computer-science-bs": "11.0701",
    "emory-data-science-bs": "30.7001",
    "emory-economics-ba": "45.0601",
    "emory-english-ba": "23.0101",
    "emory-environmental-sciences-bs": "03.0104",
    "emory-film-and-media-ba": "50.0601",
    "emory-history-ba": "54.0101",
    "emory-human-health-ba": "51.0000",
    "emory-international-studies-ba": "45.0901",
    "emory-mathematics-bs": "27.0101",
    "emory-music-ba": "50.0901",
    "emory-neuroscience-and-behavioral-biology-bs": "26.1501",
    "emory-philosophy-ba": "38.0101",
    "emory-physics-bs": "40.0801",
    "emory-political-science-bs": "45.1001",
    "emory-psychology-bs": "42.0101",
    "emory-public-policy-analysis-bs": "44.0501",
    "emory-religion-ba": "38.0201",
    "emory-sociology-ba": "45.1101",
    "emory-spanish-ba": "16.0905",
    "emory-theater-studies-ba": "50.0501",
    "emory-african-american-studies-ba": "05.0201",
    "emory-linguistics-ba": "16.0102",
    "emory-business-administration-bba": "52.0201",
    "emory-business-administration-mba": "52.0201",
    "emory-nursing-bs": "51.3801",
    "emory-public-health-mph": "51.2201",
    "emory-public-health-msph": "51.2201",
    "emory-theology-mdiv": "39.0602",
    "emory-law-prof": "22.0101",
    "emory-medicine-prof": "51.1201",
    "emory-biology-phd": "26.0101",
    "emory-computer-science-phd": "11.0701",
    "emory-economics-phd": "45.0601",
    "emory-psychology-phd": "42.0101",
    "emory-chemistry-phd": "40.0501",
    "emory-history-phd": "54.0101",
    "emory-biostatistics-phd": "26.1102",
    "emory-computer-science-ms": "11.0701",
}

# ── Universal-depth ``who_its_for`` (REPAIR_BACKLOG #4) ────────────────────────
# "Who it's for" is a UNIVERSAL depth field: every program can state the applicant it
# fits, derived from its own field, credential level, and published audience/fit material.
# A catalog-wide 0% is un-done depth, not an honest omission — so each statement below is a
# field-specific 1–2 sentence statement of the applicant the program fits (background,
# goals, readiness), NEVER a classification stub ("for students interested in {field}").
_WHO_BY_SLUG: dict[str, str] = {
    "emory-anthropology-ba": "Students curious about human cultures, evolution, and societies who want field and laboratory research and are headed toward careers in research, public health, law, or global work.",
    "emory-art-history-ba": "Students drawn to visual culture and museums who want object-based study and are aiming at curatorial, gallery, conservation, or graduate art-history paths.",
    "emory-biology-bs": "Pre-health and future life-science researchers who want laboratory experience across molecular, cellular, and ecological biology before medical or graduate school.",
    "emory-biophysics-bs": "Quantitatively minded students who want to apply physics and chemistry to living systems and are headed for research in biophysics, medicine, or the quantitative life sciences.",
    "emory-chemistry-bs": "Students strong in the physical sciences who want rigorous laboratory training and undergraduate research, preparing for chemistry graduate work, medicine, or industry.",
    "emory-classics-ba": "Students fascinated by the ancient Mediterranean who want Greek and Latin language study alongside history, literature, and archaeology, often toward law, academia, or the humanities.",
    "emory-comparative-literature-ba": "Multilingual readers and writers who want to study literature across languages and cultures and value translation and literary theory.",
    "emory-computer-science-bs": "Students who want to build software and study algorithms, AI, and systems, headed for software engineering, data, or computing research and graduate study.",
    "emory-data-science-bs": "Students who enjoy statistics, programming, and applying analysis to real problems across the sciences and want careers in data science, analytics, or quantitative research.",
    "emory-economics-ba": "Analytically minded students interested in markets, policy, and data who want theory and econometrics for careers in finance, consulting, policy, or graduate economics.",
    "emory-english-ba": "Strong readers and writers who want to study literature and sharpen critical and creative writing for careers in writing, law, education, or the humanities.",
    "emory-environmental-sciences-bs": "Students committed to sustainability and the environment who want to combine ecology, earth science, and policy for careers in conservation, consulting, or environmental research.",
    "emory-film-and-media-ba": "Students who want to both analyze and make film and media, headed toward production, media industries, criticism, or graduate study.",
    "emory-history-ba": "Students who love archives and big-picture context across regions and eras, building research and writing skills for law, education, public history, or graduate work.",
    "emory-human-health-ba": "Students interested in health, wellness, and disease across disciplines — pre-health, public health, or health-policy bound — who want an interdisciplinary foundation rather than a single science track.",
    "emory-international-studies-ba": "Globally minded students interested in world politics, economics, and culture who want language study and study abroad toward careers in diplomacy, development, or international business.",
    "emory-mathematics-bs": "Students who enjoy rigorous, abstract problem-solving and want a foundation in pure and applied mathematics for graduate study, data science, finance, or research.",
    "emory-music-ba": "Performers, composers, and scholars of music who want to combine applied study with theory and ensembles within a liberal-arts setting.",
    "emory-neuroscience-and-behavioral-biology-bs": "Students fascinated by the brain and behavior — often pre-med or research-bound — who want an interdisciplinary mix of biology, psychology, and chemistry.",
    "emory-philosophy-ba": "Students who enjoy rigorous argument about ethics, mind, and knowledge and want analytical skills useful for law, medicine, policy, or graduate philosophy.",
    "emory-physics-bs": "Students drawn to how the physical world works who want a strong foundation in classical and modern physics for research, engineering, or graduate study.",
    "emory-political-science-bs": "Students interested in government, elections, and international relations who want empirical methods and theory for careers in law, policy, government, or research.",
    "emory-psychology-bs": "Students curious about cognition, behavior, and clinical science who want laboratory research experience before careers in psychology, health, or graduate study.",
    "emory-public-policy-analysis-bs": "Students who want to evaluate and design public programs with quantitative methods, economics, and political institutions, headed toward policy, government, or graduate study.",
    "emory-religion-ba": "Students interested in the world's religious traditions, texts, and practices who want to study belief and culture comparatively, often toward law, ministry, or the humanities.",
    "emory-sociology-ba": "Students interested in inequality, institutions, and social change who want both social theory and research methods for careers in research, policy, law, or social services.",
    "emory-spanish-ba": "Students who want advanced Spanish proficiency plus the literatures and cultures of Spain and Latin America, valuable for careers in health, law, education, or international work.",
    "emory-theater-studies-ba": "Students who want to combine performance, directing, and design with dramatic literature and hands-on production work in a liberal-arts context.",
    "emory-african-american-studies-ba": "Students committed to the histories, cultures, and politics of African-descended peoples who want interdisciplinary study toward law, public service, education, or research.",
    "emory-linguistics-ba": "Students fascinated by how language works — sound, structure, and meaning — who want analytical and computational skills for tech, speech science, or graduate linguistics.",
    "emory-business-administration-bba": "High-achieving undergraduates who want a selective, STEM-designated business degree with strong consulting, finance, and healthcare placement and early career focus.",
    "emory-business-administration-mba": "Early-career professionals seeking a small-cohort, general-management MBA with strong healthcare and consulting recruiting, especially those targeting the Southeast.",
    "emory-nursing-bs": "Students committed to becoming registered nurses who want top-ranked, clinically intensive training across Emory Healthcare and are ready for a selective, fast-paced cohort.",
    "emory-public-health-mph": "Aspiring public-health practitioners and researchers who want rigorous epidemiology and biostatistics training and value Atlanta's CDC and global-health network.",
    "emory-public-health-msph": "Graduates aiming at research-oriented public-health careers who want deeper biostatistics, epidemiology, and environmental-health methods than the practice-focused MPH.",
    "emory-theology-mdiv": "Students preparing for ordained ministry or faith-based leadership who want biblical, theological, and pastoral formation, often in the Methodist tradition.",
    "emory-law-prof": "Aspiring lawyers drawn to health law, transactional and business law, or international law who want clinics and a strong Atlanta legal market.",
    "emory-medicine-prof": "Future physicians drawn to a research-intensive M.D. with strength in infectious disease, transplantation, and oncology and a dedicated research 'Discovery' phase.",
    "emory-biology-phd": "Aspiring research scientists pursuing doctoral work across molecular, cellular, and ecological biology toward academic or industry research careers.",
    "emory-computer-science-phd": "Students aiming at research careers in AI, systems, theory, or computational science who want to pursue an original dissertation with CS faculty.",
    "emory-economics-phd": "Future academic and applied economists who want rigorous doctoral training in micro, macro, and econometrics with strength in health and development economics.",
    "emory-psychology-phd": "Research-bound students pursuing doctoral work in cognition, clinical science, or systems neuroscience using behavioral and neuroimaging methods.",
    "emory-chemistry-phd": "Aspiring chemists pursuing doctoral research across synthetic, physical, biological, or materials chemistry toward academic or industry careers.",
    "emory-history-phd": "Future historians and scholars pursuing archival doctoral research across American, European, African, and global history.",
    "emory-biostatistics-phd": "Quantitatively strong students pursuing doctoral research in statistical methods for public health, clinical trials, and genomics, housed at Rollins.",
    "emory-computer-science-ms": "Graduates and professionals who want advanced computing coursework and research preparation as a step toward industry roles or a doctorate.",
}

_who_missing = [s for s in PROGRAM_SLUGS if s not in _WHO_BY_SLUG]
if _who_missing:
    raise RuntimeError(f"Emory who_its_for missing on {len(_who_missing)} rows: {_who_missing[:5]}")
_who_stray = [s for s in _WHO_BY_SLUG if s not in set(PROGRAM_SLUGS)]
if _who_stray:
    raise RuntimeError(f"Emory who_its_for has stray slugs: {_who_stray[:5]}")
_cip_missing = [s for s in PROGRAM_SLUGS if s not in _CIP_BY_SLUG]
if _cip_missing:
    raise RuntimeError(f"Emory cip_code missing on {len(_cip_missing)} rows: {_cip_missing[:5]}")
_cip_stray = [s for s in _CIP_BY_SLUG if s not in set(PROGRAM_SLUGS)]
if _cip_stray:
    raise RuntimeError(f"Emory cip_code has stray slugs: {_cip_stray[:5]}")


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
    if spec["slug"] == _FLAGSHIP:
        return dict(_REQ_MBA)
    if spec["degree_type"] == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD_GENERIC)


def apply(session: Session) -> bool:
    """Enrich Emory to the canonical profile. Flushes; caller commits."""
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
    inst.founded_year = 1836
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.emory.edu"
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
        cost_override = _COST_BY_SLUG.get(slug) or _published_grad_cost(spec)
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
                    "Published 2025-26 Emory undergraduate tuition with the financial-aid "
                    "office's cost of attendance and the College Scorecard average net price."
                ),
                "source": _COST_SRC[0],
                "source_url": _COST_SRC[1],
                "year": "2025-26",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "funded": spec["degree_type"] == "phd",
                "note": (
                    "Doctoral students at Emory are typically funded via fellowships or "
                    "assistantships when admitted; tuition is waived for funded PhD students. "
                    "See the Laney Graduate School tuition schedule for the published sticker."
                    if spec["degree_type"] == "phd"
                    else (
                        "Tuition for this graduate/professional program is published on the "
                        "school's official tuition page; a verified per-program figure is not "
                        "yet recorded here."
                    )
                ),
                "source": _BURSAR_TUITION_SRC[0],
                "source_url": _BURSAR_TUITION_SRC[1],
            }
        p.application_requirements = _requirements_for(spec)
        outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug, spec)
        p.outcomes_data = outcomes
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Matcher-core CIP join key (REPAIR_BACKLOG #1) + universal who_its_for depth (#4).
        p.cip_code = _CIP_BY_SLUG.get(slug)
        p.who_its_for = _WHO_BY_SLUG.get(slug)
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
