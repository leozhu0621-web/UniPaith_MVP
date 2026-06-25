"""Vanderbilt University — gold-standard profile data (institution + schools + program catalog).

Every value below is verified against an authoritative source (Vanderbilt's official pages,
the U.S. Dept. of Education College Scorecard / NCES for UNITID 221999, Vanderbilt Student
Accounts tuition schedules, and ranking bodies) and carries a citation, or is honestly
omitted (recorded in that node's ``_standard.omitted``) — never guessed.

Scope note (resumption clause, SKILL §"Scope & resumption"): Vanderbilt entered as a 5-stub
institution seed (five bare-field undergraduate rows — "Biomedical Engineering", "Computer
Science", "Economics", "Human and Organizational Development", "Neuroscience" — each with a
null department, 0% tuition, an empty description, and no feeds). This pass takes the
INSTITUTION fully to gold, ships a verified 5-photo campus gallery, wires working Vanderbilt
News RSS + LiveWhale events feeds, and replaces the stubs with a real, verified,
field-specific catalog of 107 programs across Vanderbilt's eleven degree-granting schools and
colleges (College of Arts and Science, School of Engineering, Peabody College of Education and
Human Development, Blair School of Music, Owen Graduate School of Management, Vanderbilt Law
School, the School of Medicine, the School of Nursing, the Divinity School, the Graduate
School, and the College of Connected Computing).

Degree designations are verified against Vanderbilt's own catalogs and school pages: the
College of Arts and Science confers the Bachelor of Arts; the School of Engineering confers
the Bachelor of Engineering (and the B.S. in Computer Science); Peabody confers the Bachelor
of Science; Blair confers the Bachelor of Music and the Bachelor of Musical Arts.

Tuition (2025-26, Vanderbilt Student Accounts): the undergraduate sticker is $67,934; the
M.D. is $70,900; the Owen M.B.A. is $74,500; the J.D. and LL.M. are $76,440. Vanderbilt bills
its other graduate programs PER CREDIT HOUR (Engineering and the Graduate School $2,419;
Peabody $2,405; Nursing $2,057; Divinity $1,193); for those tiers the matcher's annual budget
input is DERIVED as the published per-credit rate × a standard 24-credit-hour full-time year
(the same per-credit × full-time-load derivation the rest of the fleet uses) — never the
undergraduate sticker copied down. Research doctorates (Ph.D.) are funded with a full tuition
scholarship plus stipend, so Ph.D. rows are funded-omit-with-reason. A handful of programs
with a distinct, uncaptured published rate (the Executive M.B.A., the Owen specialized
master's, the School of Medicine non-M.D. health degrees, the online Ed.D., and the new online
M.S. in AI) record ``cost_data.tuition_usd`` in ``_standard.omitted`` — honestly omitted, not
guessed. No degree_type tier ships entirely null.

Reviews (``external_reviews``) are GATHERED from real, program-specific third-party coverage
for the flagship professional programs (Owen M.B.A., M.S. Finance, Master of Accountancy,
Vanderbilt Law J.D., the School of Medicine M.D., Peabody's graduate education programs, and
the School of Nursing); reviews on the remaining programs are honestly recorded
omitted-with-reason (no distinct program-specific third-party coverage) — never synthesized.
No fabricated review, quote, or figure ships.
"""

# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Vanderbilt University"
ENRICHED_AT = "2026-06-25"


def _standard(omitted: list[str] | None = None) -> dict:
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


_OMITTED_INSTITUTION: list[str] = [
    # Vanderbilt's Common Data Set test-score bands, race/ethnicity breakdown, the exact
    # applicants->admits funnel counts, and the current endowment figure were not captured
    # from a citable official page this session, so each is honestly omitted rather than
    # guessed. The College Scorecard report-card stats (admit rate, graduation rate, median
    # earnings) and the published cost of attendance are attached and cited.
    "school_outcomes.test_scores",
    "school_outcomes.demographics",
    "school_outcomes.flagship.applicants",
    "school_outcomes.flagship.admits",
    "school_outcomes.scale.endowment_usd",
    "school_outcomes.scale.faculty_count",
    "school_outcomes.top_employer_industries",
    # Vanderbilt does not publish a single "employed or continuing education" rate, and the
    # Times Higher Education world rank is reported inconsistently across recent editions, so
    # both are omitted rather than risk a wrong figure.
    "school_outcomes.employed_or_continuing_ed",
    "ranking_data.times_higher_education",
]

RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "SACSCOC",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity (R1)",
    "us_news_national": {"rank": 17, "year": 2026},
    "qs_world_university_rankings": {"rank": 250, "year": 2026},
}

SCHOOL_OUTCOMES: dict = {
    "admit_rate": 0.0586,
    "median_earnings_10yr": 91565,
    "graduation_rate_6yr": 0.9354,
    "retention_rate_first_year": 0.9634,
    "avg_net_price": 15846,
    "financial_aid": {
        "cost_of_attendance": 94274,
        "pell_grant_rate": 0.2022,
    },
    "location": {"lat": 36.14659, "lng": -86.803369, "source": "Wikipedia / Wikidata"},
    "campus_basics": {"location": "Nashville, Tennessee"},
    "scale": {
        "student_faculty_ratio": "7:1",
    },
    "research": {
        "labs": [
            "Vanderbilt Brain Institute",
            "Vanderbilt Institute of Nanoscale Science and Engineering (VINSE)",
            "Vanderbilt Institute for Energy and Environment",
            "Vanderbilt Genetics Institute",
            "the Wond'ry (innovation center)",
            "Robert Penn Warren Center for the Humanities",
        ],
        "areas": [
            "Neuroscience and brain science",
            "Nanoscale science and engineering",
            "Genetics and biomedical research",
            "Energy, environment, and sustainability",
            "Education and human development",
        ],
        "lab_links": {
            "Vanderbilt Brain Institute": "https://www.vanderbilt.edu/brain-institute/",
            "Vanderbilt Institute of Nanoscale Science and Engineering (VINSE)": "https://www.vanderbilt.edu/vinse/",
            "the Wond'ry (innovation center)": "https://www.vanderbilt.edu/thewondry/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Southeastern Conference)",
        "mascot": "Mr. Commodore (Vanderbilt Commodores)",
        "housing": "Residential campus and national arboretum in Nashville",
        "resources": [
            {"label": "Vanderbilt Commodores Athletics", "url": "https://vucommodores.com/"},
            {"label": "Jean and Alexander Heard Libraries", "url": "https://www.library.vanderbilt.edu/"},
            {"label": "the Wond'ry (innovation center)", "url": "https://www.vanderbilt.edu/thewondry/"},
            {"label": "Vanderbilt Career Center", "url": "https://www.vanderbilt.edu/career/"},
            {"label": "Vanderbilt Dyer Observatory", "url": "https://www.vanderbilt.edu/dyer/"},
        ],
    },
    "flagship": {
        "founded_year": 1873,
    },
    "campus_photos": [
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Vanderbilt_University_Campus_2017_%282%29.jpg/1920px-Vanderbilt_University_Campus_2017_%282%29.jpg",
            "credit": "Wikimedia Commons / Stablenode (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Kirkland_Hall_at_Vanderbilt_University.jpg/1920px-Kirkland_Hall_at_Vanderbilt_University.jpg",
            "credit": "Wikimedia Commons / Jaydenwithay (CC BY 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Beautiful_vanderbilt_university.jpg/1920px-Beautiful_vanderbilt_university.jpg",
            "credit": "Wikimedia Commons / Notandyarchitecture (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/VUarches.jpg/1920px-VUarches.jpg",
            "credit": "Wikimedia Commons / Dansan4444 (CC0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Benson_Science_Hall%2C_Vanderbilt_University_%282009%29.jpg/1920px-Benson_Science_Hall%2C_Vanderbilt_University_%282009%29.jpg",
            "credit": "Wikimedia Commons / Jbaker08 (public domain)",
        },
    ],
    "media_credit": "Wikimedia Commons / Stablenode (CC BY-SA 4.0)",
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Vanderbilt, UNITID 221999)",
            "url": "https://collegescorecard.ed.gov/school/?221999",
        },
        {
            "label": "NCES College Navigator — Vanderbilt University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=221999",
        },
        {
            "label": "Vanderbilt Student Accounts — Undergraduate Tuition and Fees 2025-26",
            "url": "https://www.vanderbilt.edu/stuaccts/fees/tuition_fees_2025-26_ugrd/",
        },
        {
            "label": "Vanderbilt Student Accounts — Graduate/Professional Tuition and Fees 2025-26",
            "url": "https://www.vanderbilt.edu/stuaccts/fees/tuition_fees_2025-26_grad_prof/",
        },
        {
            "label": "The Vanderbilt Hustler — Vanderbilt rises to No. 17 in 2026 U.S. News ranking",
            "url": "https://vanderbilthustler.com/2025/09/28/vanderbilt-rises-one-spot-in-2026-u-s-news-ranking-to-no-17/",
        },
        {
            "label": "QS World University Rankings 2026 — Vanderbilt University",
            "url": "https://www.topuniversities.com/universities/vanderbilt-university",
        },
    ],
}

UNDERGRAD_COUNT = 7208

DESCRIPTION = (
    "Vanderbilt University is a private research university in Nashville, Tennessee, founded "
    "in 1873 through a $1 million endowment from shipping and railroad magnate Cornelius "
    "Vanderbilt. It enrolls about 7,200 undergraduates and some 6,600 graduate and "
    "professional students on a 330-acre campus that is also a national arboretum, with a "
    "7:1 student-faculty ratio.\n\n"
    "The university is organized into ten schools and colleges plus the newly established "
    "College of Connected Computing: the College of Arts and Science, the School of "
    "Engineering, Peabody College of Education and Human Development, the Blair School of "
    "Music, the Owen Graduate School of Management, the Law School, the School of Medicine, "
    "the School of Nursing, the Divinity School, and the Graduate School. Its research is "
    "anchored by the Vanderbilt Brain Institute, the Institute of Nanoscale Science and "
    "Engineering, the Vanderbilt Genetics Institute, and the Wond'ry innovation center, and "
    "the School of Medicine ranks among the top schools nationally in NIH research funding.\n\n"
    "A Carnegie R1 university accredited by the Southern Association of Colleges and Schools "
    "Commission on Colleges, Vanderbilt ranks No. 17 among national universities by U.S. News "
    "and No. 250 in the world by QS. It admitted about 5.9% of first-year applicants and "
    "graduates about 94% of its students within six years.\n\n"
    "Vanderbilt practices need-blind admission for U.S. applicants and meets full "
    "demonstrated need through its Opportunity Vanderbilt program: against a published cost "
    "of attendance near $94,300, ten-year median earnings for federally aided students are "
    "about $91,600. The Vanderbilt Commodores compete in NCAA Division I in the Southeastern "
    "Conference."
)


_AS = "College of Arts and Science"
_ENG = "School of Engineering"
_PEABODY = "Peabody College of Education and Human Development"
_BLAIR = "Blair School of Music"
_OWEN = "Owen Graduate School of Management"
_LAW = "Vanderbilt Law School"
_MED = "Vanderbilt University School of Medicine"
_NURSING = "Vanderbilt University School of Nursing"
_DIV = "Vanderbilt Divinity School"
_GRAD = "Graduate School"
_CCC = "College of Connected Computing"

_SCHOOL_WEBSITE: dict[str, str] = {
    _AS: "https://as.vanderbilt.edu/",
    _ENG: "https://engineering.vanderbilt.edu/",
    _PEABODY: "https://peabody.vanderbilt.edu/",
    _BLAIR: "https://blair.vanderbilt.edu/",
    _OWEN: "https://business.vanderbilt.edu/",
    _LAW: "https://law.vanderbilt.edu/",
    _MED: "https://medschool.vanderbilt.edu/",
    _NURSING: "https://nursing.vanderbilt.edu/",
    _DIV: "https://divinity.vanderbilt.edu/",
    _GRAD: "https://gradschool.vanderbilt.edu/",
    _CCC: "https://computing.vanderbilt.edu/",
}

SCHOOLS: list[dict] = [
    {"name": _AS, "sort_order": 1, "description": (
        "The College of Arts and Science is Vanderbilt's largest school and the home of its "
        "undergraduate liberal-arts core, awarding the Bachelor of Arts across more than forty "
        "majors in the humanities, natural sciences, and social sciences and conferring "
        "doctoral degrees through the Graduate School."
    )},
    {"name": _ENG, "sort_order": 2, "description": (
        "The School of Engineering awards the Bachelor of Engineering and the B.S. in Computer "
        "Science alongside graduate degrees in biomedical, chemical, civil and environmental, "
        "electrical, computer, and mechanical engineering, with strengths in medical imaging, "
        "robotics, and surgical engineering."
    )},
    {"name": _PEABODY, "sort_order": 3, "description": (
        "Peabody College of Education and Human Development, consistently ranked among the top "
        "graduate schools of education in the country, awards undergraduate and graduate "
        "degrees in education, human development, special education, and learning sciences, and "
        "is home to the Vanderbilt Kennedy Center."
    )},
    {"name": _BLAIR, "sort_order": 4, "description": (
        "The Blair School of Music is Vanderbilt's conservatory-style school of music, awarding "
        "the Bachelor of Music and the Bachelor of Musical Arts in performance, composition, "
        "jazz, and integrated studies within a research-university setting."
    )},
    {"name": _OWEN, "sort_order": 5, "description": (
        "The Owen Graduate School of Management is Vanderbilt's business school, awarding the "
        "M.B.A. and specialized master's degrees in finance, accountancy, marketing, "
        "management, and health-care management, and known for its small cohorts and "
        "leadership-development curriculum."
    )},
    {"name": _LAW, "sort_order": 6, "description": (
        "Vanderbilt Law School, founded in 1874, awards the Juris Doctor and the Master of Laws "
        "and is known for a collaborative culture, strong appellate and clerkship outcomes, and "
        "interdisciplinary programs in law and economics and law and business."
    )},
    {"name": _MED, "sort_order": 7, "description": (
        "The School of Medicine awards the M.D. and graduate degrees in public health, clinical "
        "investigation, audiology, and genetic counseling, and partners with Vanderbilt "
        "University Medical Center; it ranks among the top schools nationally in NIH research "
        "support."
    )},
    {"name": _NURSING, "sort_order": 8, "description": (
        "The School of Nursing prepares advanced-practice nurses through the Master of Science "
        "in Nursing and the Doctor of Nursing Practice and trains nurse-scientists through the "
        "Ph.D. in Nursing Science, with a modified-distance model and more than a dozen clinical "
        "specialties."
    )},
    {"name": _DIV, "sort_order": 9, "description": (
        "Vanderbilt Divinity School is an ecumenical, university-based school of theology "
        "awarding the Master of Divinity, the Master of Theological Studies, and the Doctor of "
        "Ministry, with a long-standing commitment to social justice and interreligious study."
    )},
    {"name": _GRAD, "sort_order": 10, "description": (
        "The Graduate School oversees Vanderbilt's research master's and Ph.D. programs across "
        "the arts and sciences, engineering, education, and the biomedical sciences, funding "
        "doctoral students with full tuition scholarships and stipends."
    )},
    {"name": _CCC, "sort_order": 11, "description": (
        "The College of Connected Computing, established in 2024 as Vanderbilt's first new "
        "college since 1981, advances computing, data science, and artificial intelligence "
        "across the university and offers the online Master of Science in Artificial "
        "Intelligence."
    )},
]

_ABOUT_DETAIL: dict[str, dict] = {
    _AS: {
        "founded": "1873 (Vanderbilt's founding college)",
        "research_centers": [
            "Robert Penn Warren Center for the Humanities",
            "Vanderbilt Brain Institute",
            "Vanderbilt Dyer Observatory",
        ],
    },
    _ENG: {
        "founded": "Engineering instruction from 1875; reorganized as the School of Engineering in 1886",
        "research_centers": [
            "Vanderbilt Institute of Nanoscale Science and Engineering (VINSE)",
            "Vanderbilt Institute for Surgery and Engineering (VISE)",
        ],
    },
    _PEABODY: {
        "founded": "Peabody Normal School (1875); merged into Vanderbilt in 1979",
        "research_centers": ["Vanderbilt Kennedy Center", "Peabody Research Institute"],
    },
    _BLAIR: {"founded": "Blair School of Music founded 1964; joined Vanderbilt in 1981"},
    _OWEN: {
        "founded": "Owen Graduate School of Management established 1969",
    },
    _LAW: {"founded": "Vanderbilt Law School founded 1874"},
    _MED: {
        "founded": "School of Medicine founded 1874",
        "research_centers": ["Vanderbilt Genetics Institute", "Vanderbilt Institute for Clinical and Translational Research"],
    },
    _NURSING: {"founded": "School of Nursing founded 1908"},
    _DIV: {"founded": "Divinity instruction from 1875; the Divinity School organized 1915"},
    _GRAD: {"founded": "Graduate School established 1875"},
    _CCC: {"founded": "Established 2024 as Vanderbilt's first new college since 1981"},
}

_ABOUT_OMITTED: dict[str, list[str]] = {
    name: ["about_detail.leadership", "about_detail.faculty"]
    for name in _SCHOOL_WEBSITE
}
for _n in (_BLAIR, _OWEN, _LAW, _NURSING, _DIV, _GRAD, _CCC):
    _ABOUT_OMITTED[_n] = ["about_detail.leadership", "about_detail.faculty", "about_detail.research_centers"]

# Vanderbilt News RSS (https://news.vanderbilt.edu/feed/) verified 2026-06-25 returning 20
# <item>s with <enclosure> cover images (e.g. "College of Connected Computing launches Master
# of Science in AI"). Vanderbilt Events runs on LiveWhale; the iCal feed
# (https://events.vanderbilt.edu/live/ical/events) and the RSS feed both returned events the
# same day. All three confirmed to FETCH before shipping (miss #1 / miss #9).
_NEWS_RSS = "https://news.vanderbilt.edu/feed/"
_EVENTS_ICS = {"url": "https://events.vanderbilt.edu/live/ical/events", "type": "ical"}
_EVENTS_RSS = "https://events.vanderbilt.edu/live/rss/events"

_SOCIAL = {
    "instagram": "https://www.instagram.com/vanderbiltu/",
    "linkedin": "https://www.linkedin.com/school/vanderbilt-university/",
    "x": "https://twitter.com/VanderbiltU",
    "youtube": "https://www.youtube.com/vanderbiltuniversity",
    "facebook": "https://www.facebook.com/vanderbilt",
}

_SOCIAL_BY_SCHOOL: dict[str, dict] = {
    _OWEN: {
        "instagram": "https://www.instagram.com/vanderbiltmba/",
        "linkedin": "https://www.linkedin.com/school/vanderbilt-owen-graduate-school-of-management/",
    },
    _LAW: {
        "linkedin": "https://www.linkedin.com/school/vanderbilt-law-school/",
    },
    _PEABODY: {
        "instagram": "https://www.instagram.com/vanderbiltpeabody/",
        "linkedin": "https://www.linkedin.com/school/vanderbilt-peabody-college/",
    },
}

_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _AS: ["College of Arts and Science", "Vanderbilt", "liberal arts"],
    _ENG: ["School of Engineering", "Vanderbilt Engineering"],
    _PEABODY: ["Peabody College", "education", "human development"],
    _BLAIR: ["Blair School of Music", "music"],
    _OWEN: ["Owen Graduate School of Management", "Vanderbilt Business", "MBA"],
    _LAW: ["Vanderbilt Law School", "law"],
    _MED: ["School of Medicine", "Vanderbilt medicine", "VUMC"],
    _NURSING: ["School of Nursing", "VUSN", "nursing"],
    _DIV: ["Divinity School", "theology"],
    _GRAD: ["Graduate School", "PhD", "doctoral"],
    _CCC: ["College of Connected Computing", "artificial intelligence", "data science"],
}


def _school_content(name: str) -> dict:
    return {
        "news_rss": _NEWS_RSS,
        "news_url": "https://news.vanderbilt.edu/",
        "news_curated": True,
        "events_feed": dict(_EVENTS_ICS),
        "events_rss": _EVENTS_RSS,
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": _SOCIAL_BY_SCHOOL.get(name, _SOCIAL),
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


_INSTITUTION_CONTENT: dict = {
    "news_rss": _NEWS_RSS,
    "news_url": "https://news.vanderbilt.edu/",
    "news_curated": True,
    "events_feed": dict(_EVENTS_ICS),
    "events_rss": _EVENTS_RSS,
    "social": _SOCIAL,
}

# Catalog tuple: (program_name, degree_type, school, department, duration_months, slug, keywords, description)
# program_name carries Vanderbilt's real conferred designation (B.A. in A&S, B.E./B.S. in
# Engineering, B.S. in Peabody, B.M./B.M.A. in Blair, the named professional/graduate degree
# elsewhere). Departments are Vanderbilt's real owning units; descriptions are field-specific.
_CATALOG: list[tuple] = [
    # ── College of Arts and Science — Bachelor of Arts (44 majors) ──
    ("Bachelor of Arts in African American and Diaspora Studies", "bachelors", _AS,
     "Department of African American and Diaspora Studies", 48, "vanderbilt-african-american-diaspora-studies-ba",
     ["African American studies"],
     "This interdisciplinary major studies the history, politics, literature, and cultural production of people of African descent across the Americas, the Caribbean, and the African continent."),
    ("Bachelor of Arts in Anthropology", "bachelors", _AS,
     "Department of Anthropology", 48, "vanderbilt-anthropology-ba", ["anthropology"],
     "Anthropology examines human societies past and present through cultural ethnography, archaeology, and biological anthropology, with fieldwork and laboratory methods."),
    ("Bachelor of Arts in Architecture and the Built Environment", "bachelors", _AS,
     "Department of History of Art and Architecture", 48, "vanderbilt-architecture-built-environment-ba",
     ["architecture"],
     "This major pairs design studio practice with the history and theory of architecture, urbanism, and the built environment, drawing on art history, engineering, and the social sciences."),
    ("Bachelor of Arts in Art", "bachelors", _AS,
     "Department of Art", 48, "vanderbilt-art-ba", ["studio art"],
     "The studio art major develops practice across painting, drawing, sculpture, photography, and digital media alongside critique and contemporary art theory."),
    ("Bachelor of Arts in Asian American and Asian Diaspora Studies", "bachelors", _AS,
     "Program in Asian American and Asian Diaspora Studies", 48, "vanderbilt-asian-american-diaspora-studies-ba",
     ["Asian American studies"],
     "This program studies the histories, migrations, and cultural expression of Asian American and Asian diaspora communities through literature, history, and the social sciences."),
    ("Bachelor of Arts in Asian Studies", "bachelors", _AS,
     "Asian Studies Program", 48, "vanderbilt-asian-studies-ba", ["Asian studies"],
     "Asian Studies combines language study with history, religion, politics, and literature across East, South, and Southeast Asia in an area-studies framework."),
    ("Bachelor of Arts in Biochemistry and Chemical Biology", "bachelors", _AS,
     "Department of Chemistry", 48, "vanderbilt-biochemistry-chemical-biology-ba",
     ["biochemistry", "chemical biology"],
     "This major investigates the chemistry of living systems — proteins, nucleic acids, metabolism, and enzyme mechanisms — bridging chemistry and the molecular life sciences with laboratory research."),
    ("Bachelor of Arts in Biological Sciences", "bachelors", _AS,
     "Department of Biological Sciences", 48, "vanderbilt-biological-sciences-ba", ["biology"],
     "Biological Sciences spans molecular, cellular, organismal, and ecological biology, with undergraduate research across genetics, development, and evolution."),
    ("Bachelor of Arts in Chemistry", "bachelors", _AS,
     "Department of Chemistry", 48, "vanderbilt-chemistry-ba", ["chemistry"],
     "Chemistry covers organic, inorganic, physical, and analytical chemistry with hands-on laboratory work and access to research in chemical biology and materials."),
    ("Bachelor of Arts in Cinema and Media Arts", "bachelors", _AS,
     "Department of Cinema and Media Arts", 48, "vanderbilt-cinema-media-arts-ba", ["film", "media studies"],
     "Cinema and Media Arts combines the history and theory of film and screen media with hands-on production in narrative, documentary, and digital forms."),
    ("Bachelor of Arts in Classical and Mediterranean Studies", "bachelors", _AS,
     "Department of Classical and Mediterranean Studies", 48, "vanderbilt-classical-mediterranean-studies-ba",
     ["classics"],
     "This major studies the languages, literature, history, and archaeology of the ancient Greek and Roman worlds and the wider Mediterranean, including Latin and Greek."),
    ("Bachelor of Arts in Climate and Environmental Studies", "bachelors", _AS,
     "Program in Climate and Environmental Studies", 48, "vanderbilt-climate-environmental-studies-ba",
     ["climate", "environmental studies"],
     "This interdisciplinary major examines climate change and environmental challenges through the earth sciences, policy, economics, and the humanities."),
    ("Bachelor of Arts in Communication of Science and Technology", "bachelors", _AS,
     "Program in Communication of Science and Technology", 48, "vanderbilt-communication-science-technology-ba",
     ["science communication"],
     "This major trains students to translate scientific and technical work for public audiences, combining a science concentration with rhetoric, writing, and media production."),
    ("Bachelor of Arts in Communication Studies", "bachelors", _AS,
     "Department of Communication Studies", 48, "vanderbilt-communication-studies-ba", ["communication"],
     "Communication Studies analyzes rhetoric, argumentation, and human communication across interpersonal, organizational, and public contexts."),
    ("Bachelor of Arts in Culture, Advocacy, and Leadership", "bachelors", _AS,
     "Program in Culture, Advocacy, and Leadership", 48, "vanderbilt-culture-advocacy-leadership-ba",
     ["advocacy", "leadership"],
     "This major studies the cultural and ethical foundations of advocacy and leadership, pairing humanities inquiry with community-engaged practice."),
    ("Bachelor of Arts in Earth and Environmental Sciences", "bachelors", _AS,
     "Department of Earth and Environmental Sciences", 48, "vanderbilt-earth-environmental-sciences-ba",
     ["earth science", "geology"],
     "Earth and Environmental Sciences studies the solid earth, oceans, atmosphere, and climate system through geology, geochemistry, and field and laboratory research."),
    ("Bachelor of Arts in Economics", "bachelors", _AS,
     "Department of Economics", 48, "vanderbilt-economics-ba", ["economics"],
     "The economics major grounds students in microeconomic and macroeconomic theory and econometrics, with applied fields including labor, development, and public economics."),
    ("Bachelor of Arts in Economics and History", "bachelors", _AS,
     "Program in Economics and History", 48, "vanderbilt-economics-history-ba", ["economic history"],
     "This joint major reads economic questions through historical evidence and historical change through economic analysis, training students in both quantitative and archival methods."),
    ("Bachelor of Arts in English", "bachelors", _AS,
     "Department of English", 48, "vanderbilt-english-ba", ["English", "literature"],
     "English studies literature in English across periods and genres alongside critical theory, with tracks in literary studies and creative writing."),
    ("Bachelor of Arts in European Studies", "bachelors", _AS,
     "European Studies Program", 48, "vanderbilt-european-studies-ba", ["European studies"],
     "European Studies combines a European language with history, politics, and culture to study the societies and institutions of modern Europe."),
    ("Bachelor of Arts in French", "bachelors", _AS,
     "Department of French and Italian", 48, "vanderbilt-french-ba", ["French"],
     "The French major builds advanced language proficiency alongside the literature, film, and cultural history of France and the Francophone world."),
    ("Bachelor of Arts in Gender and Sexuality Studies", "bachelors", _AS,
     "Program in Gender and Sexuality Studies", 48, "vanderbilt-gender-sexuality-studies-ba",
     ["gender studies"],
     "This interdisciplinary major analyzes gender and sexuality as categories shaping culture, politics, and the body, drawing on feminist and queer theory across the humanities and social sciences."),
    ("Bachelor of Arts in German Studies", "bachelors", _AS,
     "Department of German, Russian and East European Studies", 48, "vanderbilt-german-studies-ba",
     ["German"],
     "German Studies develops language fluency alongside the literature, philosophy, and history of the German-speaking world from the Enlightenment to the present."),
    ("Bachelor of Arts in History", "bachelors", _AS,
     "Department of History", 48, "vanderbilt-history-ba", ["history"],
     "The history major trains students in archival research and interpretation across regions and eras, from the ancient world to contemporary global history."),
    ("Bachelor of Arts in History of Art", "bachelors", _AS,
     "Department of History of Art and Architecture", 48, "vanderbilt-history-of-art-ba", ["art history"],
     "History of Art studies painting, sculpture, architecture, and visual culture across periods and continents through close looking and critical interpretation."),
    ("Bachelor of Arts in Integrative Biology", "bachelors", _AS,
     "Department of Biological Sciences", 48, "vanderbilt-integrative-biology-ba", ["integrative biology"],
     "Integrative Biology studies how organisms function and evolve across scales, connecting physiology, ecology, behavior, and evolutionary biology."),
    ("Bachelor of Arts in Jewish Studies", "bachelors", _AS,
     "Program in Jewish Studies", 48, "vanderbilt-jewish-studies-ba", ["Jewish studies"],
     "Jewish Studies examines the history, religion, languages, and literature of Jewish peoples from antiquity to the modern era in an interdisciplinary framework."),
    ("Bachelor of Arts in Latin American, Caribbean, and Latinx Studies", "bachelors", _AS,
     "Program in Latin American, Caribbean, and Latinx Studies", 48, "vanderbilt-latin-american-caribbean-latinx-studies-ba",
     ["Latin American studies"],
     "This major studies the histories, politics, and cultures of Latin America, the Caribbean, and Latinx communities in the United States, integrating Spanish or Portuguese with the social sciences and humanities."),
    ("Bachelor of Arts in Law, History, and Society", "bachelors", _AS,
     "Program in Law, History, and Society", 48, "vanderbilt-law-history-society-ba", ["law and society"],
     "This interdisciplinary major studies law as a social and historical institution, examining how legal systems shape and are shaped by politics, economics, and culture."),
    ("Bachelor of Arts in Mathematics", "bachelors", _AS,
     "Department of Mathematics", 48, "vanderbilt-mathematics-ba", ["mathematics"],
     "The mathematics major develops analysis, algebra, geometry, and topology with proof-based rigor, with applied tracks toward computation and the sciences."),
    ("Bachelor of Arts in Medicine, Health, and Society", "bachelors", _AS,
     "Department of Medicine, Health, and Society", 48, "vanderbilt-medicine-health-society-ba",
     ["health studies"],
     "Medicine, Health, and Society studies health, illness, and medicine as social and cultural phenomena, drawing on the social sciences, ethics, and public health."),
    ("Bachelor of Arts in Molecular and Cellular Biology", "bachelors", _AS,
     "Department of Biological Sciences", 48, "vanderbilt-molecular-cellular-biology-ba",
     ["molecular biology"],
     "Molecular and Cellular Biology focuses on the machinery of cells — gene expression, signaling, and cellular structure — with laboratory research in molecular genetics and biochemistry."),
    ("Bachelor of Arts in Neuroscience", "bachelors", _AS,
     "Neuroscience Program", 48, "vanderbilt-neuroscience-ba", ["neuroscience"],
     "Neuroscience studies the nervous system from molecules and cells to circuits, cognition, and behavior, drawing on the Vanderbilt Brain Institute for undergraduate research."),
    ("Bachelor of Arts in Philosophy", "bachelors", _AS,
     "Department of Philosophy", 48, "vanderbilt-philosophy-ba", ["philosophy"],
     "Philosophy covers logic, ethics, metaphysics, epistemology, and the history of philosophy, with departmental strength in ethics and the philosophy of science."),
    ("Bachelor of Arts in Physics", "bachelors", _AS,
     "Department of Physics and Astronomy", 48, "vanderbilt-physics-ba", ["physics"],
     "Physics covers classical and quantum mechanics, electromagnetism, and statistical physics, with undergraduate research in astrophysics, condensed matter, and high-energy physics."),
    ("Bachelor of Arts in Political Science", "bachelors", _AS,
     "Department of Political Science", 48, "vanderbilt-political-science-ba", ["political science"],
     "Political Science studies American politics, comparative politics, international relations, and political theory, with empirical methods and a strong quantitative emphasis."),
    ("Bachelor of Arts in Public Policy Studies", "bachelors", _AS,
     "Program in Public Policy Studies", 48, "vanderbilt-public-policy-studies-ba", ["public policy"],
     "Public Policy Studies analyzes how policy is made and evaluated, combining economics, statistics, and politics to assess problems in education, health, and the economy."),
    ("Bachelor of Arts in Psychology", "bachelors", _AS,
     "Department of Psychology", 48, "vanderbilt-psychology-ba", ["psychology"],
     "Psychology studies cognition, perception, development, and social behavior using experimental and statistical methods, with laboratory research opportunities."),
    ("Bachelor of Arts in Religious Studies", "bachelors", _AS,
     "Department of Religious Studies", 48, "vanderbilt-religious-studies-ba", ["religion"],
     "Religious Studies examines religious traditions, texts, and practices across cultures and history through critical and comparative methods."),
    ("Bachelor of Arts in Russian Studies", "bachelors", _AS,
     "Department of German, Russian and East European Studies", 48, "vanderbilt-russian-studies-ba",
     ["Russian"],
     "Russian Studies pairs the Russian language with the literature, history, and politics of Russia and Eastern Europe."),
    ("Bachelor of Arts in Sociology", "bachelors", _AS,
     "Department of Sociology", 48, "vanderbilt-sociology-ba", ["sociology"],
     "Sociology examines social structure, inequality, institutions, and change, combining social theory with quantitative and qualitative research methods."),
    ("Bachelor of Arts in Spanish", "bachelors", _AS,
     "Department of Spanish and Portuguese", 48, "vanderbilt-spanish-ba", ["Spanish"],
     "The Spanish major builds advanced proficiency alongside the literatures and cultures of Spain and Latin America."),
    ("Bachelor of Arts in Spanish and Portuguese", "bachelors", _AS,
     "Department of Spanish and Portuguese", 48, "vanderbilt-spanish-portuguese-ba", ["Portuguese"],
     "This major combines Spanish and Portuguese language study with the literatures and cultures of the Iberian Peninsula, Latin America, and the Lusophone world."),
    ("Bachelor of Arts in Theatre", "bachelors", _AS,
     "Department of Theatre", 48, "vanderbilt-theatre-ba", ["theatre"],
     "Theatre integrates performance, directing, design, and dramatic literature through studio practice and main-stage production."),

    # ── School of Engineering — Bachelor of Engineering / B.S. (8) ──
    ("Bachelor of Engineering in Biomedical Engineering", "bachelors", _ENG,
     "Department of Biomedical Engineering", 48, "vanderbilt-biomedical-engineering-be",
     ["biomedical engineering"],
     "Biomedical engineering applies engineering analysis to living systems — imaging, biomechanics, biomaterials, and instrumentation — bridging the School of Engineering and the medical center."),
    ("Bachelor of Engineering in Chemical Engineering", "bachelors", _ENG,
     "Department of Chemical and Biomolecular Engineering", 48, "vanderbilt-chemical-engineering-be",
     ["chemical engineering"],
     "Chemical engineering applies thermodynamics, transport, and reaction engineering to design processes in energy, materials, and biomolecular systems."),
    ("Bachelor of Engineering in Civil Engineering", "bachelors", _ENG,
     "Department of Civil and Environmental Engineering", 48, "vanderbilt-civil-engineering-be",
     ["civil engineering"],
     "Civil engineering covers structures, geotechnics, transportation, and water resources, with design projects in infrastructure and the built environment."),
    ("Bachelor of Engineering in Computer Engineering", "bachelors", _ENG,
     "Department of Electrical and Computer Engineering", 48, "vanderbilt-computer-engineering-be",
     ["computer engineering"],
     "Computer engineering spans digital systems, computer architecture, embedded systems, and hardware-software co-design at the boundary of electrical engineering and computing."),
    ("Bachelor of Engineering in Electrical Engineering", "bachelors", _ENG,
     "Department of Electrical and Computer Engineering", 48, "vanderbilt-electrical-engineering-be",
     ["electrical engineering"],
     "Electrical engineering covers circuits, signals, electromagnetics, control, and electronics, with research in nanoscale devices and radiation-effects engineering."),
    ("Bachelor of Engineering in Mechanical Engineering", "bachelors", _ENG,
     "Department of Mechanical Engineering", 48, "vanderbilt-mechanical-engineering-be",
     ["mechanical engineering"],
     "Mechanical engineering covers solid and fluid mechanics, thermodynamics, dynamics, and design, with capstone projects in robotics, energy, and manufacturing."),
    ("Bachelor of Science in Computer Science", "bachelors", _ENG,
     "Department of Computer Science", 48, "vanderbilt-computer-science-bs", ["computer science"],
     "The ABET-accredited computer science major covers algorithms, systems, theory, and software engineering, with electives in artificial intelligence, security, and human-computer interaction."),
    ("Bachelor of Engineering Science", "bachelors", _ENG,
     "School of Engineering", 48, "vanderbilt-engineering-science-be", ["engineering science"],
     "Engineering Science is a flexible, interdisciplinary engineering degree that lets students combine engineering fundamentals with a concentration such as nanoscience, materials, or engineering management."),

    # ── Peabody College — Bachelor of Science (7) ──
    ("Bachelor of Science in Human and Organizational Development", "bachelors", _PEABODY,
     "Department of Human and Organizational Development", 48, "vanderbilt-human-organizational-development-bs",
     ["human and organizational development"],
     "Human and Organizational Development studies how people, communities, and organizations work and change, pairing social science with a required practicum internship."),
    ("Bachelor of Science in Child Development", "bachelors", _PEABODY,
     "Department of Psychology and Human Development", 48, "vanderbilt-child-development-bs",
     ["child development"],
     "Child Development studies cognitive, social, and emotional growth from infancy through adolescence, grounded in developmental psychology and applied practice."),
    ("Bachelor of Science in Child Studies", "bachelors", _PEABODY,
     "Department of Psychology and Human Development", 48, "vanderbilt-child-studies-bs", ["child studies"],
     "Child Studies examines childhood across psychology, education, policy, and health, preparing students for work in human services and child advocacy."),
    ("Bachelor of Science in Cognitive Studies", "bachelors", _PEABODY,
     "Department of Psychology and Human Development", 48, "vanderbilt-cognitive-studies-bs",
     ["cognitive studies"],
     "Cognitive Studies investigates learning, memory, and reasoning at the intersection of cognitive science, education, and neuroscience."),
    ("Bachelor of Science in Elementary Education", "bachelors", _PEABODY,
     "Department of Teaching and Learning", 48, "vanderbilt-elementary-education-bs",
     ["elementary education"],
     "Elementary Education prepares licensed teachers for the elementary grades through coursework in pedagogy, literacy, and content methods with extensive supervised classroom practice."),
    ("Bachelor of Science in Secondary Education", "bachelors", _PEABODY,
     "Department of Teaching and Learning", 48, "vanderbilt-secondary-education-bs",
     ["secondary education"],
     "Secondary Education prepares licensed teachers for middle and high school in a subject area, combining a disciplinary major with pedagogy and student teaching."),
    ("Bachelor of Science in Special Education", "bachelors", _PEABODY,
     "Department of Special Education", 48, "vanderbilt-special-education-bs", ["special education"],
     "Special Education prepares teachers to support learners with disabilities through evidence-based instruction, assessment, and intervention, drawing on the Vanderbilt Kennedy Center."),

    # ── Blair School of Music (2) ──
    ("Bachelor of Music", "bachelors", _BLAIR,
     "Blair School of Music", 48, "vanderbilt-bachelor-of-music", ["music", "performance", "composition"],
     "The Bachelor of Music trains performers, composers, and jazz musicians through applied study, ensembles, theory, and music history in a conservatory-style program within a research university."),
    ("Bachelor of Musical Arts", "bachelors", _BLAIR,
     "Blair School of Music", 48, "vanderbilt-bachelor-of-musical-arts", ["music", "interdisciplinary"],
     "The Bachelor of Musical Arts pairs intensive performance or composition study with a second area of focus outside music, giving strong musicians a flexible interdisciplinary path."),

    # ── Owen Graduate School of Management (7) ──
    ("Master of Business Administration", "professional", _OWEN,
     "Owen Graduate School of Management", 24, "vanderbilt-mba", ["MBA", "business"],
     "The two-year Owen M.B.A. is a 62-credit general-management program known for small cohorts, a structured leadership-development curriculum, and concentrations spanning finance, marketing, operations, and health care."),
    ("Executive Master of Business Administration", "professional", _OWEN,
     "Owen Graduate School of Management", 21, "vanderbilt-executive-mba", ["executive MBA"],
     "The Executive M.B.A. delivers Owen's general-management curriculum to working professionals in a weekend format, with cohorts of experienced managers and a focus on strategic leadership."),
    ("Master of Science in Finance", "masters", _OWEN,
     "Owen Graduate School of Management", 10, "vanderbilt-ms-finance", ["finance"],
     "The ten-month M.S. Finance is a STEM-designated program covering corporate finance, valuation, and capital markets, with concentrations in investment banking and quantitative finance."),
    ("Master of Accountancy", "masters", _OWEN,
     "Owen Graduate School of Management", 12, "vanderbilt-master-of-accountancy", ["accounting"],
     "The twelve-month Master of Accountancy offers Assurance and Valuation tracks, a Big Four internship, and CPA-exam preparation with one of the highest first-time pass rates among top programs."),
    ("Master of Marketing", "masters", _OWEN,
     "Owen Graduate School of Management", 10, "vanderbilt-master-of-marketing", ["marketing"],
     "The Master of Marketing trains specialists in brand management, analytics, and digital marketing through a ten-month curriculum combining strategy with quantitative methods."),
    ("Master of Management", "masters", _OWEN,
     "Owen Graduate School of Management", 10, "vanderbilt-master-of-management", ["management"],
     "The Master of Management gives recent graduates from any undergraduate background a broad foundation in business fundamentals across finance, marketing, operations, and strategy."),
    ("Master of Management in Health Care", "masters", _OWEN,
     "Owen Graduate School of Management", 12, "vanderbilt-master-management-health-care", ["health care management"],
     "This one-year program prepares physicians, nurses, and administrators to lead health-care organizations, pairing management training with health-economics and policy coursework."),

    # ── Vanderbilt Law School (2) ──
    ("Juris Doctor", "professional", _LAW,
     "Vanderbilt Law School", 36, "vanderbilt-juris-doctor", ["law", "JD"],
     "The J.D. is Vanderbilt Law's three-year program known for a collaborative culture, strong appellate-advocacy and clerkship outcomes, and joint and certificate programs in law and business and law and economics."),
    ("Master of Laws", "professional", _LAW,
     "Vanderbilt Law School", 12, "vanderbilt-master-of-laws", ["LLM", "law"],
     "The one-year LL.M. gives lawyers trained outside the United States advanced study of the American legal system alongside J.D. students, with bar-exam preparation pathways."),

    # ── School of Medicine (5) ──
    ("Doctor of Medicine", "professional", _MED,
     "Vanderbilt University School of Medicine", 48, "vanderbilt-doctor-of-medicine", ["medicine", "MD"],
     "Vanderbilt's M.D. follows the Curriculum 2.0 competency-based model with an early transition to clinical immersion and a required scholarly research project, training physicians at a top NIH-funded medical center."),
    ("Master of Public Health", "masters", _MED,
     "Vanderbilt University School of Medicine", 24, "vanderbilt-master-of-public-health", ["public health", "MPH"],
     "The M.P.H. trains practitioners in epidemiology and biostatistics with tracks in global health, epidemiology, and health policy, drawing on the Vanderbilt Institute for Medicine and Public Health."),
    ("Master of Science in Clinical Investigation", "masters", _MED,
     "Vanderbilt University School of Medicine", 24, "vanderbilt-ms-clinical-investigation", ["clinical research"],
     "This program trains physicians and scientists in the design and conduct of patient-oriented research, covering clinical trial methodology, biostatistics, and translational science."),
    ("Doctor of Audiology", "professional", _MED,
     "Department of Hearing and Speech Sciences", 48, "vanderbilt-doctor-of-audiology", ["audiology"],
     "The Au.D. prepares clinical audiologists to diagnose and treat hearing and balance disorders through coursework and supervised clinical practice at the Vanderbilt Bill Wilkerson Center."),
    ("Master of Genetic Counseling", "masters", _MED,
     "Department of Medicine", 24, "vanderbilt-master-genetic-counseling", ["genetic counseling"],
     "This program prepares genetic counselors to interpret genetic testing and support patients and families, combining medical genetics coursework with extensive supervised clinical rotations."),

    # ── School of Nursing (3) ──
    ("Master of Science in Nursing", "masters", _NURSING,
     "Vanderbilt University School of Nursing", 24, "vanderbilt-master-science-nursing", ["nursing", "MSN"],
     "The M.S.N. prepares advanced-practice nurses across more than a dozen specialties — family, adult-gerontology, pediatric, psychiatric-mental health, and nurse-midwifery among them — through a modified-distance clinical model."),
    ("Doctor of Nursing Practice", "professional", _NURSING,
     "Vanderbilt University School of Nursing", 36, "vanderbilt-doctor-nursing-practice", ["DNP"],
     "The D.N.P. is a practice doctorate preparing nurses for the highest level of clinical practice and leadership, including a nurse-anesthesia track, with a scholarly practice-improvement project."),
    ("Doctor of Philosophy in Nursing Science", "phd", _NURSING,
     "Vanderbilt University School of Nursing", 48, "vanderbilt-phd-nursing-science", ["nursing science"],
     "The Ph.D. in Nursing Science trains nurse-scientists to conduct research on health, illness, and care delivery, with funded study in research methods and a dissertation."),

    # ── Divinity School (3) ──
    ("Master of Divinity", "professional", _DIV,
     "Vanderbilt Divinity School", 36, "vanderbilt-master-of-divinity", ["divinity", "ministry"],
     "The three-year, 72-hour M.Div. prepares people for ministry and religious leadership, combining biblical and theological study with practical ministry and a commitment to social justice."),
    ("Master of Theological Studies", "masters", _DIV,
     "Vanderbilt Divinity School", 24, "vanderbilt-master-theological-studies", ["theology"],
     "The 48-hour M.T.S. is an academic theology degree offering interdisciplinary study of religion and theology, often as preparation for doctoral work or vocations beyond ordained ministry."),
    ("Doctor of Ministry", "professional", _DIV,
     "Vanderbilt Divinity School", 36, "vanderbilt-doctor-of-ministry", ["ministry"],
     "The D.Min. is an advanced professional degree for experienced ministers, integrating theological reflection with a focused project addressing a problem in ministry practice."),

    # ── College of Connected Computing (1) ──
    ("Master of Science in Artificial Intelligence", "masters", _CCC,
     "College of Connected Computing", 18, "vanderbilt-ms-artificial-intelligence", ["artificial intelligence", "AI"],
     "Launched by the College of Connected Computing, this fully online M.S. in Artificial Intelligence is built for working professionals, with a 30-credit curriculum of eight-week modules blending live and self-paced learning."),

    # ── School of Engineering — graduate (6) ──
    ("Master of Science in Biomedical Engineering", "masters", _ENG,
     "Department of Biomedical Engineering", 24, "vanderbilt-ms-biomedical-engineering", ["biomedical engineering"],
     "This graduate program advances research in biomedical imaging, biomaterials, neural engineering, and medical devices in close partnership with Vanderbilt University Medical Center."),
    ("Master of Science in Chemical Engineering", "masters", _ENG,
     "Department of Chemical and Biomolecular Engineering", 24, "vanderbilt-ms-chemical-engineering", ["chemical engineering"],
     "Graduate chemical engineering at Vanderbilt centers on advanced reaction engineering, energy and catalysis, and biomolecular and nanostructured materials research."),
    ("Master of Science in Civil and Environmental Engineering", "masters", _ENG,
     "Department of Civil and Environmental Engineering", 24, "vanderbilt-ms-civil-environmental-engineering", ["civil engineering", "environmental engineering"],
     "This program supports graduate research in structures and risk, environmental and water resources engineering, and sustainable and resilient infrastructure systems."),
    ("Master of Science in Electrical Engineering", "masters", _ENG,
     "Department of Electrical and Computer Engineering", 24, "vanderbilt-ms-electrical-engineering", ["electrical engineering"],
     "Graduate electrical engineering covers nanoscale devices, radiation effects, signal processing, and control, with research ties to VINSE and national laboratories."),
    ("Master of Science in Mechanical Engineering", "masters", _ENG,
     "Department of Mechanical Engineering", 24, "vanderbilt-ms-mechanical-engineering", ["mechanical engineering"],
     "This program advances research in medical robotics, dynamics and control, materials, and energy systems, including work at the Vanderbilt Institute for Surgery and Engineering."),
    ("Master of Science in Computer Science", "masters", _ENG,
     "Department of Computer Science", 24, "vanderbilt-ms-computer-science", ["computer science"],
     "Graduate computer science covers machine learning, systems and security, software engineering, and cyber-physical systems, with thesis and project pathways."),

    # ── Peabody College — graduate (5) ──
    ("Master of Education in Human Development Counseling", "masters", _PEABODY,
     "Department of Human and Organizational Development", 24, "vanderbilt-med-human-development-counseling", ["counseling"],
     "This M.Ed. prepares licensed professional counselors and school counselors, combining counseling theory and techniques with extensive supervised clinical practicum and internship."),
    ("Master of Education in Special Education", "masters", _PEABODY,
     "Department of Special Education", 24, "vanderbilt-med-special-education", ["special education"],
     "This M.Ed. prepares specialists and licensed teachers to serve learners with disabilities, with concentrations including high-incidence, severe disabilities, and applied behavior analysis."),
    ("Master of Education in Learning, Diversity, and Urban Studies", "masters", _PEABODY,
     "Department of Teaching and Learning", 24, "vanderbilt-med-learning-diversity-urban-studies", ["education"],
     "This M.Ed. studies teaching and learning in diverse and urban settings, preparing educators and community practitioners through coursework in equity, literacy, and community engagement."),
    ("Master of Education in Independent School Leadership", "masters", _PEABODY,
     "Department of Leadership, Policy, and Organizations", 24, "vanderbilt-med-independent-school-leadership", ["education leadership"],
     "This M.Ed. prepares leaders for independent and private schools, combining organizational leadership, finance, and governance with a school-based residency."),
    ("Doctor of Education in Leadership and Learning in Organizations", "professional", _PEABODY,
     "Department of Leadership, Policy, and Organizations", 36, "vanderbilt-edd-leadership-learning-organizations", ["education leadership"],
     "This online, executive-style Ed.D. prepares working professionals to lead in education, business, and nonprofit organizations through study of leadership, learning, data analytics, and a capstone."),

    # ── Graduate School — research doctorates (14) ──
    ("Doctor of Philosophy in Economics", "phd", _GRAD,
     "Department of Economics", 60, "vanderbilt-phd-economics", ["economics"],
     "Doctoral training in economics builds rigorous theory and econometrics toward dissertation research in fields such as labor, public, and development economics, with full funding."),
    ("Doctor of Philosophy in English", "phd", _GRAD,
     "Department of English", 60, "vanderbilt-phd-english", ["English", "literature"],
     "The English Ph.D. supports dissertation research across literary history, theory, and criticism, with strengths in American, transatlantic, and contemporary literatures."),
    ("Doctor of Philosophy in History", "phd", _GRAD,
     "Department of History", 60, "vanderbilt-phd-history", ["history"],
     "Doctoral study in history develops archival research and historiography toward a dissertation, with departmental strengths in U.S., European, and Latin American history."),
    ("Doctor of Philosophy in Philosophy", "phd", _GRAD,
     "Department of Philosophy", 60, "vanderbilt-phd-philosophy", ["philosophy"],
     "The philosophy Ph.D. trains scholars in systematic and historical philosophy, with research strengths in ethics, social and political philosophy, and the philosophy of science."),
    ("Doctor of Philosophy in Political Science", "phd", _GRAD,
     "Department of Political Science", 60, "vanderbilt-phd-political-science", ["political science"],
     "Doctoral training in political science emphasizes quantitative methods and formal theory toward dissertation research in American politics, comparative politics, and international relations."),
    ("Doctor of Philosophy in Psychological Sciences", "phd", _GRAD,
     "Department of Psychology", 60, "vanderbilt-phd-psychological-sciences", ["psychology"],
     "This Ph.D. spans cognition, neuroscience, developmental, and clinical science, with funded laboratory research drawing on the Vanderbilt Brain Institute."),
    ("Doctor of Philosophy in Sociology", "phd", _GRAD,
     "Department of Sociology", 60, "vanderbilt-phd-sociology", ["sociology"],
     "The sociology Ph.D. supports dissertation research on inequality, social movements, and political and economic sociology with advanced quantitative and qualitative methods."),
    ("Doctor of Philosophy in Anthropology", "phd", _GRAD,
     "Department of Anthropology", 60, "vanderbilt-phd-anthropology", ["anthropology"],
     "Doctoral study in anthropology trains scholars in ethnographic and archaeological research toward a dissertation, with strengths in the Americas and medical anthropology."),
    ("Doctor of Philosophy in Religion", "phd", _GRAD,
     "Graduate Department of Religion", 60, "vanderbilt-phd-religion", ["religion"],
     "The Ph.D. in Religion offers doctoral research across biblical studies, theology, ethics, and the historical and comparative study of religion, in partnership with the Divinity School."),
    ("Doctor of Philosophy in Mathematics", "phd", _GRAD,
     "Department of Mathematics", 60, "vanderbilt-phd-mathematics", ["mathematics"],
     "Doctoral study in mathematics centers on dissertation research in areas including operator algebras, topology, and mathematical analysis, with full funding."),
    ("Doctor of Philosophy in Physics", "phd", _GRAD,
     "Department of Physics and Astronomy", 60, "vanderbilt-phd-physics", ["physics"],
     "The physics Ph.D. supports funded research in astrophysics, condensed-matter, high-energy, and biological physics, including access to the Dyer Observatory and national facilities."),
    ("Doctor of Philosophy in Chemistry", "phd", _GRAD,
     "Department of Chemistry", 60, "vanderbilt-phd-chemistry", ["chemistry"],
     "Doctoral research in chemistry spans organic, inorganic, physical, and chemical biology, with strengths in synthesis, catalysis, and the Vanderbilt Institute of Chemical Biology."),
    ("Doctor of Philosophy in Biological Sciences", "phd", _GRAD,
     "Department of Biological Sciences", 60, "vanderbilt-phd-biological-sciences", ["biology"],
     "This Ph.D. funds dissertation research in genetics, developmental biology, cell biology, and evolution, with interdisciplinary training across the life-sciences institutes."),
    ("Doctor of Philosophy in Neuroscience", "phd", _GRAD,
     "Vanderbilt Brain Institute", 60, "vanderbilt-phd-neuroscience", ["neuroscience"],
     "Administered through the Vanderbilt Brain Institute, this Ph.D. funds research from molecular and cellular neuroscience to systems, cognitive, and computational neuroscience."),
]


def _build_catalog() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    seen_names: set[tuple[str, str]] = set()
    for pname, dtype, school, dept, dur, slug, kw, desc in _CATALOG:
        if slug in seen:
            raise RuntimeError(f"duplicate slug {slug}")
        seen.add(slug)
        key = (pname, dtype)
        if key in seen_names:
            raise RuntimeError(f"duplicate (program_name, degree_type) {key}")
        seen_names.add(key)
        out.append({
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": dept,
            "duration_months": dur,
            "delivery_format": "online" if slug == "vanderbilt-ms-artificial-intelligence" else "on_campus",
            "keywords": list(kw),
            "description": desc,
        })
    return out


PROGRAMS: list[dict] = _build_catalog()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

_TUITION_UG = 67934
_UNDERGRAD_COA = 94274
_UG_SRC = (
    "Vanderbilt Student Accounts — Undergraduate Tuition and Fees 2025-26",
    "https://www.vanderbilt.edu/stuaccts/fees/tuition_fees_2025-26_ugrd/",
)
_GRAD_PROF_SRC = (
    "Vanderbilt Student Accounts — Graduate/Professional Tuition and Fees 2025-26",
    "https://www.vanderbilt.edu/stuaccts/fees/tuition_fees_2025-26_grad_prof/",
)
_MED_SRC = (
    "Vanderbilt Student Accounts — Medical School Tuition and Fees 2025-26",
    "https://www.vanderbilt.edu/stuaccts/fees/tuition_fees_2025-26_medical/",
)
_MBA_SRC = (
    "Vanderbilt Business — M.B.A. Tuition, Loans and Scholarships",
    "https://business.vanderbilt.edu/mba/admissions/tuition-financing-scholarships/",
)
_LAW_SRC = (
    "Vanderbilt Law School — J.D. Costs and Financial Aid",
    "https://law.vanderbilt.edu/jd-program/costs-financial-aid/",
)

_MD_ANNUAL = 70900
_MBA_ANNUAL = 74500
_JD_ANNUAL = 76440
_LLM_ANNUAL = 76440  # LL.M. billed at the Law School per-year rate

# A standard full-time graduate academic year at Vanderbilt is 24 credit hours (12 per
# semester). Vanderbilt bills its non-flat graduate tuition PER CREDIT HOUR, so the
# matcher's annual budget input is derived as (published per-credit rate × 24) — the same
# "per-credit × full-time load" derivation the fleet uses (cf. Dartmouth's per-term × terms).
# The exact per-credit rate is published and cited; the 24-hour full-time year is stated in
# every note. Research doctorates are funded (omit-with-reason) and a handful of programs with
# a distinct, uncaptured published rate are honestly omitted (see _TUITION_OMIT_SLUGS).
_FULL_TIME_CREDITS = 24
_PER_CREDIT_RATE: dict[str, int] = {
    _ENG: 2419,      # Engineering / Graduate School per credit hour (2025-26)
    _PEABODY: 2405,  # Peabody College per credit hour (2025-26)
    _NURSING: 2057,  # School of Nursing per credit hour (2025-26)
    _DIV: 1193,      # Divinity School per credit hour (2025-26)
}

# Programs whose published tuition is a distinct per-program / lockstep / online rate not
# captured from a citable Vanderbilt page this session, or (M.S.-AI) a new online rate — the
# tuition is honestly omitted-with-reason rather than guessed. None of these zeros out a whole
# degree_type tier: the master's and professional tiers are filled by the derived per-credit
# rows and the verified professional flats above.
_TUITION_OMIT_SLUGS: set[str] = {
    "vanderbilt-executive-mba",              # Executive M.B.A. lockstep program total (not captured)
    "vanderbilt-ms-finance",                 # Owen specialized-master's per-program rate (not captured)
    "vanderbilt-master-of-accountancy",
    "vanderbilt-master-of-marketing",
    "vanderbilt-master-of-management",
    "vanderbilt-master-management-health-care",
    "vanderbilt-master-of-public-health",    # School of Medicine graduate-health rate (not captured)
    "vanderbilt-ms-clinical-investigation",
    "vanderbilt-master-genetic-counseling",
    "vanderbilt-doctor-of-audiology",
    "vanderbilt-edd-leadership-learning-organizations",  # online executive Ed.D. fixed rate (not captured)
    "vanderbilt-ms-artificial-intelligence",             # new fully online M.S.-AI rate (not captured)
}


def _annual_cost(tuition_usd: int, *, note: str, source: str, source_url: str, year: str = "2025-26") -> dict:
    return {
        "tuition_usd": tuition_usd,
        "funded": False,
        "note": note,
        "source": source,
        "source_url": source_url,
        "year": year,
    }


# Programs with a verified, published flat annual tuition figure the matcher can read directly
# as an annual budget input (never the undergraduate sticker copied down). Per-credit-billed
# graduate programs (Engineering, Peabody, Nursing, Divinity) are ADDED below by derivation.
_COST_BY_SLUG: dict[str, dict] = {
    "vanderbilt-doctor-of-medicine": _annual_cost(
        _MD_ANNUAL,
        note=(
            f"School of Medicine M.D. tuition: ${_MD_ANNUAL:,} per academic year (2025-26), "
            "distinct from and higher than the undergraduate rate."
        ),
        source=_MED_SRC[0],
        source_url=_MED_SRC[1],
    ),
    "vanderbilt-mba": _annual_cost(
        _MBA_ANNUAL,
        note=(
            f"Owen Graduate School of Management M.B.A. tuition: ${_MBA_ANNUAL:,} per year "
            "(2025-26)."
        ),
        source=_MBA_SRC[0],
        source_url=_MBA_SRC[1],
    ),
    "vanderbilt-juris-doctor": _annual_cost(
        _JD_ANNUAL,
        note=(
            f"Vanderbilt Law School J.D. tuition: ${_JD_ANNUAL:,} per academic year (2025-26)."
        ),
        source=_LAW_SRC[0],
        source_url=_LAW_SRC[1],
    ),
    "vanderbilt-master-of-laws": _annual_cost(
        _LLM_ANNUAL,
        note=(
            f"Vanderbilt Law School LL.M. tuition is billed at the Law School per-year rate of "
            f"${_LLM_ANNUAL:,} (2025-26)."
        ),
        source=_LAW_SRC[0],
        source_url=_LAW_SRC[1],
    ),
}


def _build_derived_costs() -> None:
    """Add per-credit-derived annual tuition for the per-credit-billed graduate programs
    (Engineering, Peabody, Nursing, Divinity), excluding the funded Ph.D. tier and the
    honestly-omitted slugs. Annual = published per-credit rate × a standard 24-credit-hour
    full-time year. Idempotent at import."""
    for spec in PROGRAMS:
        slug = spec["slug"]
        if slug in _COST_BY_SLUG or slug in _TUITION_OMIT_SLUGS:
            continue
        if spec["degree_type"] not in ("masters", "professional"):
            continue
        rate = _PER_CREDIT_RATE.get(spec["school"])
        if rate is None:
            continue
        annual = rate * _FULL_TIME_CREDITS
        _COST_BY_SLUG[slug] = _annual_cost(
            annual,
            note=(
                f"Vanderbilt bills {spec['school']} graduate tuition at ${rate:,} per credit hour "
                f"(2025-26); the annual full-time figure is ${annual:,} at a standard "
                f"{_FULL_TIME_CREDITS}-credit-hour full-time academic year (12 hours per semester)."
            ),
            source=_GRAD_PROF_SRC[0],
            source_url=_GRAD_PROF_SRC[1],
        )


def _grad_has_verified_tuition(spec: dict) -> bool:
    return spec["slug"] in _COST_BY_SLUG


_build_derived_costs()


_OUTCOMES_CONDITIONS = (
    "Institution-wide median earnings of federally aided students measured 10 years after entry "
    "(U.S. Dept. of Education College Scorecard); not a program-specific figure."
)
_OUTCOMES_INSTITUTION = {
    "median_salary": 91565,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": _OUTCOMES_CONDITIONS,
    "source": "U.S. Dept. of Education College Scorecard (Vanderbilt, UNITID 221999)",
    "source_url": "https://collegescorecard.ed.gov/school/?221999",
}

_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or QuestBridge Application",
        "Vanderbilt writing supplement",
        "Secondary-school report + transcript",
        "Teacher and counselor recommendations",
        "SAT or ACT scores (verify the current testing policy on the admissions site)",
    ],
    "deadlines": {
        "early_decision_1": "November 1",
        "early_decision_2": "January 1",
        "regular_decision": "January 1",
    },
    "source": "https://admissions.vanderbilt.edu/apply/",
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
    "source": "https://gradschool.vanderbilt.edu/admissions/",
}
_REQ_MED = {
    "materials": [
        "AMCAS application",
        "Vanderbilt secondary application",
        "MCAT scores",
        "Letters of recommendation",
        "Interview",
    ],
    "deadlines": {
        "amcas": "Verify the current AMCAS cycle on the School of Medicine admissions site.",
    },
    "source": "https://medschool.vanderbilt.edu/admissions/",
}
_REQ_LAW = {
    "materials": [
        "LSAC application + CAS report",
        "LSAT or GRE scores",
        "Personal statement",
        "Letters of recommendation",
        "Transcripts",
    ],
    "deadlines": {
        "note": "Rolling admission; see the Vanderbilt Law admissions site for the current cycle.",
    },
    "source": "https://law.vanderbilt.edu/admissions/",
}
_REQ_MBA = {
    "materials": [
        "Owen online application",
        "GMAT, GRE, or Executive Assessment scores (waivers available)",
        "Essays",
        "Letters of recommendation",
        "Resume + transcripts",
    ],
    "deadlines": {
        "note": "Multiple admission rounds; see the Owen admissions site for the current cycle.",
    },
    "source": "https://business.vanderbilt.edu/mba/admissions/",
}

_TRACKS_BY_SLUG: dict[str, dict] = {
    "vanderbilt-bachelor-of-music": {
        "tracks": ["Performance", "Composition", "Jazz Studies", "Integrated Studies", "Integrated Studies / Teacher Education"],
        "source": "Blair School of Music — Bachelor of Music",
        "source_url": "https://blair.vanderbilt.edu/bachelor-of-music/",
    },
    "vanderbilt-master-science-nursing": {
        "tracks": [
            "Family Nurse Practitioner", "Adult-Gerontology Primary Care NP",
            "Adult-Gerontology Acute Care NP", "Pediatric NP (Primary and Acute Care)",
            "Neonatal NP", "Psychiatric-Mental Health NP", "Emergency NP",
            "Nurse-Midwifery", "Women's Health NP", "Nursing Informatics",
            "Nursing and Health Care Leadership",
        ],
        "source": "Vanderbilt School of Nursing — Specialties",
        "source_url": "https://nursing.vanderbilt.edu/programs/specialties/",
    },
    "vanderbilt-master-of-accountancy": {
        "tracks": ["Assurance", "Valuation"],
        "source": "Vanderbilt Business — Master of Accountancy",
        "source_url": "https://business.vanderbilt.edu/masters-in-accounting/",
    },
}
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}
_FACULTY_BY_SLUG: dict[str, dict] = {}

# external_reviews are GATHERED from real, program-specific third-party coverage and distilled
# to an honest paragraph + themes (with the common cautions) and cited per source. No quote,
# rating, or theme is fabricated.
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "vanderbilt-mba": {
        "summary": (
            "Vanderbilt's Owen M.B.A. is a small, full-time program prized for its "
            "leadership-development curriculum and tight community; the Class of 2024 reported an "
            "average starting base salary of about $150,000, with roughly 90% of job-seekers "
            "holding offers within three months of graduation. Students and reviewers consistently "
            "praise the personal attention from faculty and career services and a 'competitive, "
            "not cutthroat' culture, and Owen scores highly in Princeton Review surveys for campus "
            "environment and quality of life. The most common caution is a direct consequence of "
            "the program's size: some employers recruit less heavily on campus than at the largest "
            "M.B.A. programs, so students targeting certain roles report doing extra outreach, and "
            "placement and salary dipped slightly for the Class of 2024 from the prior year."
        ),
        "themes": [
            {"label": "Leadership development", "sentiment": "positive",
             "detail": "The structured Leadership Development Program and leadership coursework are repeatedly cited as a distinctive strength that helps students understand their strengths and goals."},
            {"label": "Small, personal community", "sentiment": "positive",
             "detail": "The small cohort means students get to know each other and receive close attention from faculty and career services, which is the program's signature draw."},
            {"label": "Strong employment outcomes", "sentiment": "positive",
             "detail": "The Class of 2024 reported an average base salary near $150,000, with about 90% of job-seekers accepting offers within three months of graduation."},
            {"label": "Collaborative culture", "sentiment": "positive",
             "detail": "Students describe a 'competitive, not cutthroat' environment, and Owen scores near the top of Princeton Review surveys for campus environment and quality of life."},
            {"label": "Smaller on-campus recruiting footprint", "sentiment": "caution",
             "detail": "Because the program is small, some employers have a lighter on-campus presence than at the largest programs, so students may need extra legwork for certain roles."},
            {"label": "Recent placement softening", "sentiment": "mixed",
             "detail": "Placement and average salary slipped modestly for the Class of 2024 from a school-record prior year, tracking the broader M.B.A. hiring market."},
        ],
        "sources": [
            {"label": "Vanderbilt Business — M.B.A. Employment / Outcomes", "url": "https://business.vanderbilt.edu/mba/vanderbilt-advantage/exceptional-outcomes/"},
            {"label": "Poets&Quants — Vanderbilt Owen 2024 MBA placement & salary", "url": "https://poetsandquants.com/2024/11/25/setbacks-in-2024-placement-salary-for-grads-of-another-top-u-s-mba-program/"},
            {"label": "Fortune — Vanderbilt MBA salaries hit a record high", "url": "https://fortune.com/education/articles/vanderbilt-mba-salaries-hit-a-record-high-grads-see-170k-plus-starting-pay-packages/"},
            {"label": "GMAT Club — Owen Vanderbilt MBA student reviews", "url": "https://gmatclub.com/reviews/business_school/owen-35"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
    },
    "vanderbilt-ms-finance": {
        "summary": (
            "Vanderbilt's M.S. Finance is a STEM-designated, ten-month program with strong, "
            "well-documented placement: 97% of job-seeking Class of 2025 graduates secured "
            "full-time offers within six months, reporting an average base salary near $94,000, "
            "with nearly half entering investment banking and top hires at firms including Wells "
            "Fargo, JPMorgan Chase, and KPMG. Reviewers value the program's compact curriculum, "
            "Owen's small-cohort attention, and the investment-banking and quantitative-finance "
            "concentrations. The common caution is intensity: the program is fast-paced and "
            "recruiting begins almost immediately, so it rewards applicants who arrive with a "
            "clear finance goal."
        ),
        "themes": [
            {"label": "Strong, documented placement", "sentiment": "positive",
             "detail": "97% of job-seeking Class of 2025 graduates secured full-time offers within six months, with 46% entering investment banking."},
            {"label": "STEM-designated curriculum", "sentiment": "positive",
             "detail": "The STEM designation supports international students' work eligibility and reflects the program's quantitative focus."},
            {"label": "Small-cohort attention", "sentiment": "positive",
             "detail": "Like the M.B.A., the M.S. Finance benefits from Owen's small size and close career-services support."},
            {"label": "Fast-paced and recruiting-intensive", "sentiment": "caution",
             "detail": "The ten-month timeline means recruiting starts almost immediately, which rewards students who enter with a defined goal."},
        ],
        "sources": [
            {"label": "Vanderbilt Business — M.S. Finance Class of 2025 outcomes", "url": "https://business.vanderbilt.edu/news/2026/01/29/vanderbilt-ms-finance-class-of-2025-delivers-strong-employment-outcomes/"},
            {"label": "Masters in Finance HQ — Vanderbilt MSF career outcomes", "url": "https://msfhq.com/vanderbilt-university-msf-2024-career-outcomes/"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
    },
    "vanderbilt-master-of-accountancy": {
        "summary": (
            "Vanderbilt's Master of Accountancy is a twelve-month program with two tracks "
            "(Assurance and Valuation) and exceptionally consistent outcomes: it reports near-100% "
            "employment year after year, with most graduates beginning at a Big Four firm, and one "
            "of the highest first-time CPA pass rates among top programs (about 90% versus roughly "
            "50% nationally). Reviewers highlight the structured Big Four internship and CPA "
            "preparation built into the year. The main caution is fit: the program is purpose-built "
            "for public-accounting careers, so it is strongest for students aiming at that path "
            "rather than a broader business degree."
        ),
        "themes": [
            {"label": "Near-universal Big Four placement", "sentiment": "positive",
             "detail": "The program reports near-100% employment annually, with most graduates starting at a Big Four accounting firm."},
            {"label": "High CPA pass rate", "sentiment": "positive",
             "detail": "About 90% of graduates pass the CPA exam on the first try, well above the national average, supported by built-in exam preparation."},
            {"label": "Integrated internship", "sentiment": "positive",
             "detail": "A 10-week paid Big Four internship is embedded in the 12-month curriculum alongside the degree and CPA preparation."},
            {"label": "Narrow by design", "sentiment": "caution",
             "detail": "The program is purpose-built for public accounting, so it suits students committed to that career path more than those seeking a general business degree."},
        ],
        "sources": [
            {"label": "Vanderbilt Business — Master of Accountancy", "url": "https://business.vanderbilt.edu/masters-in-accounting/"},
            {"label": "Accountingedu — best accounting master's for Big Four placement", "url": "https://www.accountingedu.org/best-accounting-masters-big-four-placement/"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
    },
    "vanderbilt-juris-doctor": {
        "summary": (
            "Vanderbilt Law's J.D. is a consistently top-15 program (No. 12 in the 2026 U.S. News "
            "ranking) known for a collaborative culture and strong employment outcomes: about 94% "
            "of the Class of 2024 obtained full-time, long-term, bar-passage-required jobs nine "
            "months after graduation, and the school ranks among the national leaders in federal "
            "clerkship placement (roughly 9% of the class). Princeton Review surveys rank "
            "Vanderbilt near the top for classroom experience and quality of life. The common "
            "caution is market reach: the school places powerfully in the Southeast and nationally "
            "in clerkships and large firms, but its regional pull is strongest in the South, so "
            "students targeting specific other markets should weigh that."
        ),
        "themes": [
            {"label": "Top-15 reputation", "sentiment": "positive",
             "detail": "Vanderbilt Law ranked No. 12 in the 2026 U.S. News Best Law Schools list, consistently placing in the top 15."},
            {"label": "Strong employment outcomes", "sentiment": "positive",
             "detail": "About 94% of the Class of 2024 secured full-time, long-term, bar-passage-required positions nine months after graduation."},
            {"label": "Federal clerkships", "sentiment": "positive",
             "detail": "The school is among the national leaders in federal clerkship placement, with roughly 9% of the class clerking."},
            {"label": "Collaborative culture and quality of life", "sentiment": "positive",
             "detail": "Princeton Review surveys place Vanderbilt near the top nationally for classroom experience and quality of life, reflecting a non-cutthroat culture."},
            {"label": "Regional concentration", "sentiment": "mixed",
             "detail": "While it places nationally in clerkships and large firms, the school's regional pull is strongest in the Southeast."},
        ],
        "sources": [
            {"label": "Vanderbilt Law — Employment Report", "url": "https://law.vanderbilt.edu/career-services/employment-report/"},
            {"label": "U.S. News — Vanderbilt Law School", "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/vanderbilt-university-03147"},
            {"label": "The Vanderbilt Hustler — Law ranks No. 12 in 2026 U.S. News", "url": "https://vanderbilthustler.com/2026/04/16/law-school-ranks-no-12-in-2026-u-s-news-rankings/"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
    },
    "vanderbilt-doctor-of-medicine": {
        "summary": (
            "Vanderbilt's M.D. is a top-tier research medical program built on the Curriculum 2.0 "
            "model, which moves students into clinical immersion early and requires an integrated "
            "scholarly research project; it sits at a medical center that ranks among the top "
            "handful of schools nationally in NIH research funding. Reviewers point to the "
            "research environment, the integrated curriculum, and Vanderbilt University Medical "
            "Center's clinical breadth. Common cautions are the high cost of attendance typical of "
            "private medical schools and the research-heavy orientation, which is a strength for "
            "academically minded students but a consideration for those set on primary-care "
            "practice."
        ),
        "themes": [
            {"label": "Top NIH research funding", "sentiment": "positive",
             "detail": "The School of Medicine ranks among the top schools nationally in total NIH research support, anchoring a deep research environment."},
            {"label": "Curriculum 2.0", "sentiment": "positive",
             "detail": "A competency-based curriculum moves students into clinical immersion early and requires an integrated scholarly research project."},
            {"label": "Clinical breadth at VUMC", "sentiment": "positive",
             "detail": "Training at Vanderbilt University Medical Center gives students access to a large academic medical center and its specialties."},
            {"label": "High cost of attendance", "sentiment": "caution",
             "detail": "M.D. tuition of about $70,900 plus living costs reflects the high all-in cost typical of private medical schools."},
            {"label": "Research-forward orientation", "sentiment": "mixed",
             "detail": "The program's research emphasis is a strength for academically minded students and a consideration for those focused on primary-care practice."},
        ],
        "sources": [
            {"label": "U.S. News — Vanderbilt School of Medicine", "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/vanderbilt-university-04109"},
            {"label": "Vanderbilt Health News — VUSM among top in NIH research funding", "url": "https://news.vumc.org/2026/02/24/vanderbilt-university-school-of-medicine-ranks-seventh-in-nih-support-of-disease-fighting-research/"},
            {"label": "Vanderbilt Student Accounts — Medical School Tuition 2025-26", "url": "https://www.vanderbilt.edu/stuaccts/fees/tuition_fees_2025-26_medical/"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
    },
    "vanderbilt-doctor-nursing-practice": {
        "summary": (
            "Vanderbilt's School of Nursing is a national leader, with its master's program ranked "
            "No. 5 and its D.N.P. ranked in the top 20 by U.S. News; the D.N.P. prepares nurses for "
            "the highest level of clinical practice and leadership, including a nurse-anesthesia "
            "track. Reviewers highlight the school's modified-distance model — which blends online "
            "coursework with intensive on-campus sessions and local clinical placements — and its "
            "breadth of specialties. The common caution is the clinical and travel demand: students "
            "must arrange and attend substantial in-person clinical hours, which requires planning "
            "for working nurses."
        ),
        "themes": [
            {"label": "Top-ranked nursing school", "sentiment": "positive",
             "detail": "U.S. News ranks Vanderbilt's master's nursing program No. 5 and its D.N.P. in the top 20 nationally."},
            {"label": "Modified-distance model", "sentiment": "positive",
             "detail": "The program blends online coursework with on-campus intensives and local clinical placements, supporting students across the country."},
            {"label": "Breadth of specialties", "sentiment": "positive",
             "detail": "Pathways span advanced practice and leadership, including a nurse-anesthesia track within the D.N.P."},
            {"label": "Clinical and travel demand", "sentiment": "caution",
             "detail": "Substantial in-person clinical hours and on-campus intensives require planning, particularly for working nurses."},
        ],
        "sources": [
            {"label": "U.S. News — Vanderbilt nursing (DNP)", "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/vanderbilt-university-33271/dnp"},
            {"label": "Vanderbilt School of Nursing — Doctor of Nursing Practice", "url": "https://nursing.vanderbilt.edu/programs/dnp/"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
    },
    "vanderbilt-med-human-development-counseling": {
        "summary": (
            "Peabody College is consistently ranked among the very top graduate schools of "
            "education in the country (No. 5 by U.S. News in 2025, and No. 1 in several recent "
            "years), and its Human Development Counseling M.Ed. prepares licensed professional and "
            "school counselors through a clinically intensive curriculum. Reviewers cite Peabody's "
            "research reputation, faculty access, and the supervised practicum and internship that "
            "anchor the degree. The common cautions are cost — Peabody bills graduate tuition per "
            "credit hour at a premium rate — and the heavy clinical-hour requirement typical of "
            "counselor licensure."
        ),
        "themes": [
            {"label": "Top-ranked education school", "sentiment": "positive",
             "detail": "Peabody ranks No. 5 by U.S. News in 2025 and has held the No. 1 spot in several recent years, lending the degree strong national standing."},
            {"label": "Clinically intensive training", "sentiment": "positive",
             "detail": "The program is built around supervised practicum and internship hours that prepare graduates for professional and school-counseling licensure."},
            {"label": "Faculty and research access", "sentiment": "positive",
             "detail": "Students work with leading education and human-development faculty and Peabody's research centers, including the Vanderbilt Kennedy Center."},
            {"label": "Premium per-credit cost", "sentiment": "caution",
             "detail": "Peabody bills graduate tuition per credit hour at a premium rate, so total program cost is a planning consideration."},
        ],
        "sources": [
            {"label": "U.S. News — Vanderbilt (Peabody) Best Education Schools", "url": "https://www.usnews.com/best-graduate-schools/top-education-schools/vanderbilt-university-06191"},
            {"label": "Peabody College — Ranked Among the Best", "url": "https://peabody.vanderbilt.edu/about/ranked_among_the_best.php"},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party and official sources — not individual verbatim reviews.",
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
    if spec["slug"] == "vanderbilt-doctor-of-medicine":
        return dict(_REQ_MED)
    if spec["school"] == _LAW:
        return dict(_REQ_LAW)
    if spec["school"] == _OWEN:
        return dict(_REQ_MBA)
    return dict(_REQ_GRAD_GENERIC)


def apply(session: Session) -> bool:
    """Enrich Vanderbilt to the canonical profile. Flushes; caller commits."""
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
    inst.founded_year = 1873
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.vanderbilt.edu"
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
                "breakdown": {
                    "tuition": _TUITION_UG,
                    "total_cost_of_attendance": _UNDERGRAD_COA,
                },
                "funded": False,
                "note": (
                    "Published 2025-26 Vanderbilt undergraduate tuition with Student Accounts' "
                    "cost of attendance."
                ),
                "source": _UG_SRC[0],
                "source_url": _UG_SRC[1],
                "year": "2025-26",
            }
        elif spec["degree_type"] == "phd":
            p.tuition = None
            p.cost_data = {
                "funded": True,
                "note": (
                    "Vanderbilt research-doctoral students receive a full tuition scholarship plus "
                    "a stipend within the funding-guarantee period, so tuition is waived for funded "
                    "Ph.D. students; the published graduate per-credit rate is $2,419 (2025-26)."
                ),
                "source": _GRAD_PROF_SRC[0],
                "source_url": _GRAD_PROF_SRC[1],
                "year": "2025-26",
            }
        else:
            # _TUITION_OMIT_SLUGS — a distinct per-program / lockstep / online published rate
            # not captured from a citable Vanderbilt page this session; omitted-with-reason
            # (cost_data.tuition_usd is recorded in _standard.omitted) rather than guessed.
            p.tuition = None
            p.cost_data = {
                "funded": False,
                "note": (
                    "This program is billed at a distinct published per-program rate that was not "
                    "captured from a citable Vanderbilt page this session, so a single verified "
                    "annual tuition figure is honestly omitted rather than guessed; see the "
                    "program's official admissions/cost page for the current rate."
                ),
                "source": _GRAD_PROF_SRC[0],
                "source_url": _GRAD_PROF_SRC[1],
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
