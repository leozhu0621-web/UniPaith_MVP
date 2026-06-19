"""Duke University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``dukeprof4`` migration to merge
``DEPTH_REVIEWS`` into ``duke_profile._REVIEWS_BY_SLUG`` for 42
remaining coverable programs (50/50 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "duke-accelerated-daytime-mba-ms": {
        "summary": "Students describe Fuqua's Accelerated Daytime MBA as a one-year, STEM-designated MBA for candidates with strong quantitative backgrounds; praise includes Team Fuqua culture and finance/consulting placement (Class of 2025 median base $160,000), with cautions that the compressed timeline limits internships and the brand trails M7 peers in some national markets.",
        "themes": [
            {
                "label": "One-year format",
                "sentiment": "positive",
                "detail": "Accelerated schedule suits candidates with prior business or quantitative training.",
            },
            {
                "label": "Team Fuqua culture",
                "sentiment": "positive",
                "detail": "Collaborative, values-driven community with team-based learning.",
            },
            {
                "label": "Finance & consulting outcomes",
                "sentiment": "positive",
                "detail": "Class of 2025: $160K median base; financial services and consulting are top destinations.",
            },
            {
                "label": "Compressed timeline",
                "sentiment": "caution",
                "detail": "One-year pace limits traditional summer internships and deep specialization.",
            },
            {
                "label": "Brand vs. M7 peers",
                "sentiment": "mixed",
                "detail": "Strong outcomes but a smaller national MBA brand than M7 schools in some markets.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 Accelerated Daytime MBA",
                "url": "https://www.fuqua.duke.edu/programs/accelerated-daytime-mba",
            },
            {
                "label": "Poets&Quants \u2014 Duke Fuqua",
                "url": "https://poetsandquants.com/schools/duke-universitys-fuqua-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-biomedical-engineering-bse": {
        "summary": "Students describe Duke's Engineering in Biomedical Engineering B.S.E. within Pratt as a rigorous engineering degree at a selective private R1 university; praise includes undergraduate research access and Triangle tech recruiting, with cautions about demanding prerequisites and a smaller engineering community than large public tech schools.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Pratt departments.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Small Pratt cohort",
                "sentiment": "positive",
                "detail": "Close faculty access on a research-university campus.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Pratt is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Biomedical Engineering",
                "url": "https://bme.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-biomedical-engineering-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Biomedical Engineering as a research degree at an R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about competitive admission, five-plus-year timelines, and funding competition.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Duke's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Biomedical Engineering",
                "url": "https://bme.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-civil-and-environmental-engineering-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Civil & Environmental Engineering as a research degree at an R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about competitive admission, five-plus-year timelines, and funding competition.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Duke's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Civil & Environmental Engineering",
                "url": "https://cee.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-civil-engineering-bse": {
        "summary": "Students describe Duke's Engineering in Civil Engineering B.S.E. within Pratt as a rigorous engineering degree at a selective private R1 university; praise includes undergraduate research access and Triangle tech recruiting, with cautions about demanding prerequisites and a smaller engineering community than large public tech schools.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Pratt departments.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Small Pratt cohort",
                "sentiment": "positive",
                "detail": "Close faculty access on a research-university campus.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Pratt is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Civil Engineering",
                "url": "https://cee.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-computer-science-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Computer Science as a research degree with strengths in AI, systems, and computational biology \u2014 U.S. News ranks Duke CS graduate #20; praise includes interdisciplinary ties to medicine and engineering, with cautions about funding competition and a smaller department than CS-flagship giants.",
        "themes": [
            {
                "label": "AI & systems research",
                "sentiment": "positive",
                "detail": "Faculty lead research in AI, systems, and computational biology.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich applied CS research.",
            },
            {
                "label": "Graduate CS rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke CS graduate program #20.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke CS.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than MIT, Stanford, or CMU CS departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke CS \u2014 Graduate Programs",
                "url": "https://cs.duke.edu/grad",
            },
            {
                "label": "Duke CS \u2014 About the Department",
                "url": "https://cs.duke.edu/about",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-data-science-mathematics-and-computer-science-ab": {
        "summary": "Students describe Duke's Data Science: Mathematics & Computer Science major as a quantitatively rigorous interdisciplinary degree bridging statistics, CS, and applied math \u2014 Niche ranks Duke #15 for undergraduate CS (2026); praise includes research access and flexible AI/data-science concentrations, with cautions about demanding prerequisites and a newer major with evolving course offerings.",
        "themes": [
            {
                "label": "Interdisciplinary rigor",
                "sentiment": "positive",
                "detail": "Combines mathematics, statistics, and computer science foundations.",
            },
            {
                "label": "AI & data-science focus",
                "sentiment": "positive",
                "detail": "Concentrations align with growing analytics and ML hiring.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Students join CS and statistics faculty research groups.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Quantitative gateway sequences are competitive and theory-heavy.",
            },
            {
                "label": "Evolving curriculum",
                "sentiment": "mixed",
                "detail": "Newer major still expanding specialized elective offerings.",
            },
        ],
        "sources": [
            {
                "label": "Duke CS \u2014 Undergraduate",
                "url": "https://cs.duke.edu/undergrad",
            },
            {
                "label": "Niche \u2014 Best Colleges for Computer Science",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-doctor-of-juridical-science-sjd-phd": {
        "summary": "Legal scholars describe Duke Law's Doctor of Juridical Science (SJD) as an advanced research degree for candidates pursuing academic legal careers; praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about extremely competitive law-faculty hiring and a small cohort relative to large public law schools.",
        "themes": [
            {
                "label": "Legal scholarship",
                "sentiment": "positive",
                "detail": "SJD candidates produce dissertation-level legal research.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Close advisor relationships with Duke Law faculty.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Sanford, Fuqua, and Medicine enrich law-and-policy research.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are highly competitive.",
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": "Fewer SJD students than large public law schools.",
            },
        ],
        "sources": [
            {
                "label": "Duke Law \u2014 SJD Program",
                "url": "https://law.duke.edu/academics/sjd/",
            },
            {
                "label": "U.S. News \u2014 Duke Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-doctor-of-nursing-practice-dnp-prof": {
        "summary": "Advanced-practice nurses describe Duke's Doctor of Nursing Practice (DNP) as a terminal clinical doctorate \u2014 U.S. News ranks Duke Nursing among top graduate nursing schools; praise includes evidence-based practice projects and Duke Hospital leadership training, with cautions about balancing clinical work with doctoral coursework and regional variation in DNP hiring expectations.",
        "themes": [
            {
                "label": "Clinical doctorate",
                "sentiment": "positive",
                "detail": "DNP prepares advanced-practice leaders for clinical and executive roles.",
            },
            {
                "label": "Evidence-based projects",
                "sentiment": "positive",
                "detail": "Capstone projects apply research to clinical quality improvement.",
            },
            {
                "label": "Duke Hospital access",
                "sentiment": "positive",
                "detail": "Clinical training at a top academic medical center.",
            },
            {
                "label": "Work-study balance",
                "sentiment": "caution",
                "detail": "Practicing nurses must balance clinical shifts with doctoral coursework.",
            },
            {
                "label": "Employer expectations",
                "sentiment": "mixed",
                "detail": "DNP hiring requirements vary by health system and region.",
            },
        ],
        "sources": [
            {
                "label": "Duke School of Nursing \u2014 DNP Program",
                "url": "https://nursing.duke.edu/academics/programs/dnp",
            },
            {
                "label": "U.S. News \u2014 Duke Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-doctor-of-nursing-practice-nurse-anesthesia-prof": {
        "summary": "Students describe Duke's Doctor of Nursing Practice \u2014 Nurse Anesthesia as a highly selective CRNA program \u2014 U.S. News ranks Duke Nursing among top graduate nursing schools; praise includes extensive clinical anesthesia training at Duke University Hospital, with cautions about program intensity, competitive admission, and CRNA job-market shifts in some regions.",
        "themes": [
            {
                "label": "CRNA training",
                "sentiment": "positive",
                "detail": "Program prepares certified registered nurse anesthetists with extensive clinical hours.",
            },
            {
                "label": "Hospital clinical access",
                "sentiment": "positive",
                "detail": "Duke University Hospital provides diverse anesthesia cases.",
            },
            {
                "label": "Top nursing rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke among leading graduate nursing schools.",
            },
            {
                "label": "Program intensity",
                "sentiment": "caution",
                "detail": "Anesthesia training demands sustained clinical and academic commitment.",
            },
            {
                "label": "Job-market shifts",
                "sentiment": "mixed",
                "detail": "CRNA hiring and autonomy rules vary by state and health system.",
            },
        ],
        "sources": [
            {
                "label": "Duke School of Nursing \u2014 Nurse Anesthesia DNP",
                "url": "https://nursing.duke.edu/academics/programs/nurse-anesthesia-dnp",
            },
            {
                "label": "U.S. News \u2014 Duke Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-economics-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Economics as a research degree at an R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about competitive admission, five-plus-year timelines, and funding competition.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Duke's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Economics",
                "url": "https://econ.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/duke-university-2920",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-electrical-and-computer-engineering-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Electrical & Computer Engineering as a research degree at an R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about competitive admission, five-plus-year timelines, and funding competition.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Duke's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Electrical & Computer Engineering",
                "url": "https://ece.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-environmental-engineering-bse": {
        "summary": "Students describe Duke's Engineering in Environmental Engineering B.S.E. within Pratt as a rigorous engineering degree at a selective private R1 university; praise includes undergraduate research access and Triangle tech recruiting, with cautions about demanding prerequisites and a smaller engineering community than large public tech schools.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Pratt departments.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Small Pratt cohort",
                "sentiment": "positive",
                "detail": "Close faculty access on a research-university campus.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Pratt is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Environmental Engineering",
                "url": "https://cee.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-interdisciplinary-engineering-and-applied-science-ideas-bse": {
        "summary": "Students describe Duke's Engineering in Interdisciplinary Engineering & Applied Science (IDEAS) B.S.E. within Pratt as a rigorous engineering degree at a selective private R1 university; praise includes undergraduate research access and Triangle tech recruiting, with cautions about demanding prerequisites and a smaller engineering community than large public tech schools.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Pratt departments.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Small Pratt cohort",
                "sentiment": "positive",
                "detail": "Close faculty access on a research-university campus.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Pratt is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Interdisciplinary Engineering & Applied Science (IDEAS)",
                "url": "https://pratt.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-jd-llm-in-international-and-comparative-law-prof": {
        "summary": "Students describe Duke's joint JD/LLM in International & Comparative Law as a four-year program combining the JD with advanced international-law training; praise includes Duke Law's #7 national rank and global-law faculty, with cautions about extended time in school and a specialized career path versus a standard JD.",
        "themes": [
            {
                "label": "International law depth",
                "sentiment": "positive",
                "detail": "Joint degree adds advanced coursework in comparative and international law.",
            },
            {
                "label": "Top law school rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke Law #7 nationally (2026).",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Experiential clinics build practical international-law skills.",
            },
            {
                "label": "Extended timeline",
                "sentiment": "caution",
                "detail": "Four-year program adds a year beyond the standard three-year JD.",
            },
            {
                "label": "Specialized career path",
                "sentiment": "mixed",
                "detail": "Best suited for international-law careers rather than general Big Law.",
            },
        ],
        "sources": [
            {
                "label": "Duke Law \u2014 JD/LLM International & Comparative Law",
                "url": "https://law.duke.edu/academics/llm/jdllm/",
            },
            {
                "label": "U.S. News \u2014 Duke Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-jd-llm-in-law-and-entrepreneurship-prof": {
        "summary": "Students describe Duke's joint JD/LLM in Law & Entrepreneurship as a program combining legal training with startup and venture-capital law; praise includes Duke's entrepreneurship clinics and Research Triangle startup ecosystem, with cautions about a niche career focus and fewer traditional Big Law slots than generalist JD paths.",
        "themes": [
            {
                "label": "Entrepreneurship law",
                "sentiment": "positive",
                "detail": "Curriculum covers venture finance, IP, and startup governance.",
            },
            {
                "label": "Triangle startup ecosystem",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects students to tech and biotech ventures.",
            },
            {
                "label": "Clinical experience",
                "sentiment": "positive",
                "detail": "Startup Law Clinic provides hands-on venture-law practice.",
            },
            {
                "label": "Niche career focus",
                "sentiment": "caution",
                "detail": "Best suited for startup/VC law rather than general Big Law.",
            },
            {
                "label": "Extended timeline",
                "sentiment": "mixed",
                "detail": "Joint degree adds time beyond the standard three-year JD.",
            },
        ],
        "sources": [
            {
                "label": "Duke Law \u2014 JD/LLM Law & Entrepreneurship",
                "url": "https://law.duke.edu/academics/llm/jdllm-entrepreneurship/",
            },
            {
                "label": "Duke Law \u2014 Start-Up Ventures Clinic",
                "url": "https://law.duke.edu/students/clinics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-linguistics-and-computer-science-ab": {
        "summary": "Students describe Duke's Linguistics & Computer Science interdepartmental major as a niche interdisciplinary degree bridging NLP, computational linguistics, and formal language theory; praise includes CS department research in AI/NLP and small seminars, with cautions about a smaller peer cohort than standalone CS and limited dedicated course offerings compared with larger NLP programs.",
        "themes": [
            {
                "label": "NLP & linguistics bridge",
                "sentiment": "positive",
                "detail": "Combines formal linguistics with computational and AI methods.",
            },
            {
                "label": "CS research access",
                "sentiment": "positive",
                "detail": "Students join NLP and AI labs within Duke CS.",
            },
            {
                "label": "Small seminars",
                "sentiment": "positive",
                "detail": "Interdisciplinary major attracts motivated, specialized students.",
            },
            {
                "label": "Limited course depth",
                "sentiment": "caution",
                "detail": "Fewer dedicated NLP courses than at CMU or Stanford.",
            },
            {
                "label": "Niche career path",
                "sentiment": "mixed",
                "detail": "Best suited for NLP/CL research or graduate study.",
            },
        ],
        "sources": [
            {
                "label": "Duke CS \u2014 Undergraduate",
                "url": "https://cs.duke.edu/undergrad",
            },
            {
                "label": "Duke Linguistics Program",
                "url": "https://linguistics.duke.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-in-business-climate-and-sustainability-mbcs-ms": {
        "summary": "Students describe Fuqua's Master in Business, Climate, and Sustainability (MBCS) as a specialized business master's bridging finance, policy, and environmental science; praise includes Duke's Nicholas School ties and growing ESG recruiting, with cautions that the field is evolving quickly and employer demand varies by sector and region.",
        "themes": [
            {
                "label": "ESG focus",
                "sentiment": "positive",
                "detail": "Curriculum connects climate science, policy, and business strategy.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Nicholas School and Sanford faculty enrich sustainability coursework.",
            },
            {
                "label": "Emerging recruiting",
                "sentiment": "positive",
                "detail": "Energy, consulting, and impact-investing firms hire sustainability talent.",
            },
            {
                "label": "Field evolution",
                "sentiment": "caution",
                "detail": "ESG hiring cycles and regulatory frameworks shift rapidly.",
            },
            {
                "label": "Niche market",
                "sentiment": "mixed",
                "detail": "Fewer dedicated roles than traditional finance or consulting tracks.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 MBCS program",
                "url": "https://www.fuqua.duke.edu/programs/master-business-climate-sustainability",
            },
            {
                "label": "Nicholas School of the Environment",
                "url": "https://nicholas.duke.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-biomedical-sciences-mbs-ms": {
        "summary": "Post-baccalaureate students describe Duke's Master of Biomedical Sciences (MBS) as a one-year bridge program for medical and health-sciences careers; praise includes Duke Medicine faculty access and a structured pre-med curriculum, with cautions that it is a credential-enhancement program rather than a direct medical school admission guarantee.",
        "themes": [
            {
                "label": "Pre-med bridge",
                "sentiment": "positive",
                "detail": "Structured coursework strengthens medical-school applications.",
            },
            {
                "label": "Duke Medicine access",
                "sentiment": "positive",
                "detail": "Faculty and hospital resources enrich biomedical training.",
            },
            {
                "label": "One-year format",
                "sentiment": "positive",
                "detail": "Accelerated timeline suits career changers and gap-year students.",
            },
            {
                "label": "No admission guarantee",
                "sentiment": "caution",
                "detail": "Completion does not guarantee medical-school admission.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Students typically self-fund without research assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Master of Biomedical Sciences",
                "url": "https://medschool.duke.edu/education/health-professions-education-programs/master-biomedical-sciences",
            },
            {
                "label": "U.S. News \u2014 Duke Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/duke-university-04018",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-divinity-mdiv-ms": {
        "summary": "Students describe Duke Divinity School's Master of Divinity (MDiv) as a theologically rigorous program within Duke University \u2014 U.S. News ranks Duke #7 among national universities (2026); praise includes Wesleyan and Anglican traditions, field education, and Duke Chapel community, with cautions about demanding coursework and variable placement in ordained ministry versus nonprofit leadership.",
        "themes": [
            {
                "label": "Theological rigor",
                "sentiment": "positive",
                "detail": "MDiv curriculum spans scripture, theology, ethics, and pastoral practice.",
            },
            {
                "label": "Field education",
                "sentiment": "positive",
                "detail": "Supervised ministry placements connect classroom learning to congregations.",
            },
            {
                "label": "Duke Chapel community",
                "sentiment": "positive",
                "detail": "Campus worship and Duke University resources enrich the experience.",
            },
            {
                "label": "Ministry placement variability",
                "sentiment": "mixed",
                "detail": "Ordination paths and job markets vary by denomination and region.",
            },
            {
                "label": "Academic workload",
                "sentiment": "caution",
                "detail": "Three-year MDiv combines coursework, field education, and language study.",
            },
        ],
        "sources": [
            {
                "label": "Duke Divinity \u2014 MDiv Program",
                "url": "https://divinity.duke.edu/academics/mdiv",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/duke-university-2920",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-engineering-in-ai-for-product-innovation-ms": {
        "summary": "Students describe Duke's Master of Engineering in AI for Product Innovation as a STEM-designated professional master's blending AI, product design, and entrepreneurship; praise includes Pratt's industry partnerships and Research Triangle tech recruiting, with cautions about self-funded tuition and competition with dedicated MS in CS programs at peer schools.",
        "themes": [
            {
                "label": "AI product focus",
                "sentiment": "positive",
                "detail": "Curriculum connects machine learning to product development and innovation.",
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": "STEM status extends OPT eligibility for eligible international graduates.",
            },
            {
                "label": "Triangle tech recruiting",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects graduates to tech and biotech firms.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional MEng students typically self-fund without assistantships.",
            },
            {
                "label": "Peer competition",
                "sentiment": "mixed",
                "detail": "Dedicated MS CS programs at peer schools compete for similar roles.",
            },
        ],
        "sources": [
            {
                "label": "Duke MEng \u2014 AI for Product Innovation",
                "url": "https://meng.duke.edu/degrees/ai-product-innovation",
            },
            {
                "label": "Pratt School of Engineering",
                "url": "https://pratt.duke.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-engineering-in-civil-engineering-ms": {
        "summary": "Graduate students describe Duke's Master of Engineering in Civil Engineering within Pratt as a professional coursework degree; praise includes Triangle tech and biotech recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Pratt engineering reputation",
                "sentiment": "positive",
                "detail": "Pratt ranks among leading private engineering schools.",
            },
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects graduates to tech and biotech firms.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS/MEng",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Civil Engineering",
                "url": "https://cee.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-engineering-in-cybersecurity-ms": {
        "summary": "Professionals describe Duke's Master of Engineering in Cybersecurity as a coursework-focused MEng blending security engineering, policy, and hands-on labs; praise includes Pratt faculty research and Triangle defense/tech recruiting, with cautions about self-funded tuition and a rapidly evolving threat landscape that requires continuous learning beyond the degree.",
        "themes": [
            {
                "label": "Security engineering",
                "sentiment": "positive",
                "detail": "Curriculum covers cryptography, network security, and secure systems design.",
            },
            {
                "label": "Hands-on labs",
                "sentiment": "positive",
                "detail": "Practical projects simulate real-world security challenges.",
            },
            {
                "label": "Triangle recruiting",
                "sentiment": "positive",
                "detail": "Defense, tech, and healthcare firms hire security engineers in the RTP area.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional MEng students typically self-fund without assistantships.",
            },
            {
                "label": "Rapid field change",
                "sentiment": "mixed",
                "detail": "Cybersecurity requires ongoing certification and skill updates post-graduation.",
            },
        ],
        "sources": [
            {
                "label": "Duke MEng \u2014 Cybersecurity",
                "url": "https://meng.duke.edu/degrees/cybersecurity",
            },
            {
                "label": "Pratt School of Engineering",
                "url": "https://pratt.duke.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-engineering-in-financial-technology-ms": {
        "summary": "Students describe Duke's Master of Engineering in Financial Technology as a STEM-designated MEng bridging quantitative finance, software engineering, and data science; praise includes Fuqua ties and finance-recruiting access, with cautions about self-funded tuition and Durham's distance from Wall Street recruiting hubs.",
        "themes": [
            {
                "label": "FinTech focus",
                "sentiment": "positive",
                "detail": "Curriculum connects quantitative finance, ML, and software engineering.",
            },
            {
                "label": "Fuqua ties",
                "sentiment": "positive",
                "detail": "Business-school resources enrich finance and entrepreneurship coursework.",
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": "STEM status extends OPT eligibility for eligible international graduates.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional MEng students typically self-fund without assistantships.",
            },
            {
                "label": "Finance hub distance",
                "sentiment": "mixed",
                "detail": "Durham is strong for RTP tech but quieter for Wall Street recruiting.",
            },
        ],
        "sources": [
            {
                "label": "Duke MEng \u2014 Financial Technology",
                "url": "https://meng.duke.edu/degrees/financial-technology",
            },
            {
                "label": "Fuqua School of Business",
                "url": "https://www.fuqua.duke.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-engineering-management-ms": {
        "summary": "Graduate students describe Duke's Master of Engineering Management within Pratt as a research and coursework degree; praise includes Triangle tech and biotech recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Pratt engineering reputation",
                "sentiment": "positive",
                "detail": "Pratt ranks among leading private engineering schools.",
            },
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects graduates to tech and biotech firms.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS/MEng",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Engineering Management",
                "url": "https://meng.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-laws-llm-ms": {
        "summary": "International lawyers describe Duke Law's LLM as a one-year advanced law degree with strong faculty in international, environmental, and business law \u2014 U.S. News ranks Duke Law #7 nationally (2026); praise includes clinical offerings and a collegial community, with cautions about high tuition and limited U.S. bar-exam pathways for some foreign-trained lawyers.",
        "themes": [
            {
                "label": "Top-tier national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke Law #7 nationally (2026).",
            },
            {
                "label": "International law strength",
                "sentiment": "positive",
                "detail": "Faculty and centers focus on global and comparative law.",
            },
            {
                "label": "Collegial community",
                "sentiment": "positive",
                "detail": "Small LLM cohort integrates with JD students in seminars and clinics.",
            },
            {
                "label": "Tuition & visa",
                "sentiment": "caution",
                "detail": "High tuition and visa constraints for post-LLM U.S. employment.",
            },
            {
                "label": "Bar exam pathways",
                "sentiment": "mixed",
                "detail": "Eligibility varies by home-country credentials and state bar rules.",
            },
        ],
        "sources": [
            {
                "label": "Duke Law \u2014 LLM Program",
                "url": "https://law.duke.edu/academics/llm/",
            },
            {
                "label": "U.S. News \u2014 Duke Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-management-studies-foundations-of-business-ms": {
        "summary": "Recent graduates describe Fuqua's Master of Management Studies: Foundations of Business as a pre-experience business master's for non-business undergraduates; praise includes Team Fuqua culture and a bridge to Fuqua's MBA recruiting, with cautions that it is not a substitute for work experience in traditional MBA pipelines and outcomes vary by prior academic background.",
        "themes": [
            {
                "label": "Pre-experience bridge",
                "sentiment": "positive",
                "detail": "Designed for recent graduates without full-time business experience.",
            },
            {
                "label": "Team Fuqua culture",
                "sentiment": "positive",
                "detail": "Collaborative cohort experience mirrors Fuqua MBA values.",
            },
            {
                "label": "Business foundations",
                "sentiment": "positive",
                "detail": "Core coursework spans finance, marketing, strategy, and analytics.",
            },
            {
                "label": "MBA pipeline limits",
                "sentiment": "caution",
                "detail": "Not equivalent to work experience expected by top MBA employers.",
            },
            {
                "label": "Outcome variability",
                "sentiment": "mixed",
                "detail": "Placement depends heavily on undergraduate major and internship history.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 Master of Management Studies",
                "url": "https://www.fuqua.duke.edu/programs/master-management-studies",
            },
            {
                "label": "Poets&Quants \u2014 Duke Fuqua",
                "url": "https://poetsandquants.com/schools/duke-universitys-fuqua-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-nursing-mn-pre-licensure-ms": {
        "summary": "Students describe Duke's Master of Nursing (MN, pre-licensure) as an accelerated entry-to-nursing program \u2014 U.S. News ranks Duke Nursing among top graduate nursing schools; praise includes clinical training at Duke University Hospital and simulation labs, with cautions about an intensive accelerated pace and competitive admission.",
        "themes": [
            {
                "label": "Accelerated entry",
                "sentiment": "positive",
                "detail": "Career changers earn an MN and RN licensure in an accelerated format.",
            },
            {
                "label": "Clinical training",
                "sentiment": "positive",
                "detail": "Duke University Hospital provides hands-on clinical rotations.",
            },
            {
                "label": "Top nursing rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke among leading graduate nursing schools.",
            },
            {
                "label": "Intensive pace",
                "sentiment": "caution",
                "detail": "Accelerated curriculum demands sustained clinical and coursework load.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Competitive pool for a small cohort.",
            },
        ],
        "sources": [
            {
                "label": "Duke School of Nursing \u2014 MN Program",
                "url": "https://nursing.duke.edu/academics/programs/master-nursing",
            },
            {
                "label": "U.S. News \u2014 Duke Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-quantitative-management-business-analytics-ms": {
        "summary": "Students describe Fuqua's Master of Quantitative Management: Business Analytics as a STEM-designated, data-intensive business master's with strong placement in consulting and tech analytics roles; praise includes Team Fuqua collaboration and quantitative rigor, with cautions about a fast-paced curriculum and competition with dedicated data-science master's programs at peer schools.",
        "themes": [
            {
                "label": "Analytics rigor",
                "sentiment": "positive",
                "detail": "STEM-designated curriculum emphasizes statistics, ML, and business applications.",
            },
            {
                "label": "Consulting & tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter analytics, consulting, and product roles at major firms.",
            },
            {
                "label": "Team Fuqua culture",
                "sentiment": "positive",
                "detail": "Collaborative cohort projects mirror MBA team-based learning.",
            },
            {
                "label": "Intensive pace",
                "sentiment": "caution",
                "detail": "Quantitative core and practicum projects move quickly in a one-year format.",
            },
            {
                "label": "Peer competition",
                "sentiment": "mixed",
                "detail": "Dedicated MS in analytics programs at CMU and MIT compete for similar roles.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 MSQM Business Analytics",
                "url": "https://www.fuqua.duke.edu/programs/master-quantitative-management-business-analytics",
            },
            {
                "label": "Poets&Quants \u2014 Duke Fuqua",
                "url": "https://poetsandquants.com/schools/duke-universitys-fuqua-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-science-in-nursing-msn-ms": {
        "summary": "Registered nurses describe Duke's Master of Science in Nursing (MSN) as an advanced-practice nursing degree with specialty tracks \u2014 U.S. News ranks Duke Nursing among top graduate nursing schools; praise includes Duke Hospital clinical access and faculty research, with cautions about demanding clinical hours and regional licensing requirements for advanced-practice roles.",
        "themes": [
            {
                "label": "Advanced practice tracks",
                "sentiment": "positive",
                "detail": "MSN specialties include nurse practitioner and clinical leadership paths.",
            },
            {
                "label": "Clinical access",
                "sentiment": "positive",
                "detail": "Duke University Hospital supports advanced clinical training.",
            },
            {
                "label": "Research faculty",
                "sentiment": "positive",
                "detail": "School of Nursing faculty lead health-services and clinical research.",
            },
            {
                "label": "Clinical hours",
                "sentiment": "caution",
                "detail": "Advanced-practice tracks require extensive supervised clinical hours.",
            },
            {
                "label": "Licensing variation",
                "sentiment": "mixed",
                "detail": "NP scope-of-practice rules vary by state after graduation.",
            },
        ],
        "sources": [
            {
                "label": "Duke School of Nursing \u2014 MSN Program",
                "url": "https://nursing.duke.edu/academics/programs/msn",
            },
            {
                "label": "U.S. News \u2014 Duke Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-science-in-biomedical-engineering-ms": {
        "summary": "Graduate students describe Duke's Master's in Biomedical Engineering within Pratt as a research and coursework degree; praise includes Triangle tech and biotech recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Pratt engineering reputation",
                "sentiment": "positive",
                "detail": "Pratt ranks among leading private engineering schools.",
            },
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects graduates to tech and biotech firms.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS/MEng",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Biomedical Engineering",
                "url": "https://bme.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-science-in-electrical-and-computer-engineering-ms": {
        "summary": "Graduate students describe Duke's Master's in Electrical & Computer Engineering within Pratt as a research and coursework degree; praise includes Triangle tech and biotech recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Pratt engineering reputation",
                "sentiment": "positive",
                "detail": "Pratt ranks among leading private engineering schools.",
            },
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects graduates to tech and biotech firms.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS/MEng",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Electrical & Computer Engineering",
                "url": "https://ece.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-master-of-science-in-mechanical-engineering-and-materials-science-ms": {
        "summary": "Graduate students describe Duke's Master's in Mechanical Engineering & Materials Science within Pratt as a research and coursework degree; praise includes Triangle tech and biotech recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Pratt engineering reputation",
                "sentiment": "positive",
                "detail": "Pratt ranks among leading private engineering schools.",
            },
            {
                "label": "Research & industry access",
                "sentiment": "positive",
                "detail": "Research Triangle Park connects graduates to tech and biotech firms.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS/MEng",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Mechanical Engineering",
                "url": "https://mems.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-materials-science-and-engineering-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Materials Science & Engineering as a research degree at an R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about competitive admission, five-plus-year timelines, and funding competition.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Duke's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Materials Science & Engineering",
                "url": "https://mems.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-mechanical-engineering-and-materials-science-grad-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Mechanical Engineering & Materials Science as a research degree at an R1 university ranked #7 nationally by U.S. News (2026); praise includes faculty mentorship and interdisciplinary Duke resources, with cautions about competitive admission, five-plus-year timelines, and funding competition.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Duke's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Medicine, engineering, and policy schools enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Duke departments.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Mechanical Engineering & Materials Science",
                "url": "https://mems.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-mechanical-engineering-bse": {
        "summary": "Students describe Duke's Engineering in Mechanical Engineering B.S.E. within Pratt as a rigorous engineering degree at a selective private R1 university; praise includes undergraduate research access and Triangle tech recruiting, with cautions about demanding prerequisites and a smaller engineering community than large public tech schools.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Pratt departments.",
            },
            {
                "label": "Tech placement",
                "sentiment": "positive",
                "detail": "Graduates enter tech, consulting, and graduate programs.",
            },
            {
                "label": "Small Pratt cohort",
                "sentiment": "positive",
                "detail": "Close faculty access on a research-university campus.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Structured engineering core limits early electives.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Pratt is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Duke \u2014 Mechanical Engineering",
                "url": "https://mems.duke.edu/",
            },
            {
                "label": "U.S. News \u2014 Duke University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-medical-scientist-training-program-md-phd-phd": {
        "summary": "Applicants describe Duke's Medical Scientist Training Program (MD-PhD) as a dual-degree physician-scientist track \u2014 U.S. News ranks Duke Medicine #6 for research (2025); praise includes integrated clinical and research training through Duke University Hospital and DCRI, with cautions about eight-plus-year timelines and extremely competitive admission.",
        "themes": [
            {
                "label": "Physician-scientist training",
                "sentiment": "positive",
                "detail": "Integrated MD and Ph.D. curriculum trains clinician-researchers.",
            },
            {
                "label": "Top research ranking",
                "sentiment": "positive",
                "detail": "U.S. News ranks Duke #6 among medical schools for research (2025).",
            },
            {
                "label": "DCRI integration",
                "sentiment": "positive",
                "detail": "Duke Clinical Research Institute supports translational research.",
            },
            {
                "label": "Extended timeline",
                "sentiment": "caution",
                "detail": "MD-PhD programs commonly span eight or more years.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission requires exceptional research and clinical credentials.",
            },
        ],
        "sources": [
            {
                "label": "Duke MSTP \u2014 MD-PhD Program",
                "url": "https://medschool.duke.edu/education/health-professions-education-programs/medical-scientist-training-program",
            },
            {
                "label": "U.S. News \u2014 Duke Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/duke-university-04018",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-msqm-business-analytics-online-ms": {
        "summary": "Working professionals describe Fuqua's online MSQM: Business Analytics as a part-time, STEM-designated analytics degree with live virtual classes; praise includes flexibility for working analysts and Fuqua's recruiting network, with cautions that online delivery reduces spontaneous networking versus the residential MSQM and that self-paced modules require strong time management.",
        "themes": [
            {
                "label": "Flexible online format",
                "sentiment": "positive",
                "detail": "Part-time schedule suits working professionals in analytics roles.",
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": "STEM status extends OPT eligibility for eligible international graduates.",
            },
            {
                "label": "Fuqua network",
                "sentiment": "positive",
                "detail": "Access to Fuqua alumni and recruiting resources.",
            },
            {
                "label": "Networking trade-off",
                "sentiment": "caution",
                "detail": "Virtual format limits informal campus networking versus residential MSQM.",
            },
            {
                "label": "Self-directed pace",
                "sentiment": "mixed",
                "detail": "Part-time students must balance coursework with full-time jobs.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 MSQM Business Analytics (online)",
                "url": "https://www.fuqua.duke.edu/programs/msqm-business-analytics-online",
            },
            {
                "label": "Poets&Quants \u2014 Duke Fuqua",
                "url": "https://poetsandquants.com/schools/duke-universitys-fuqua-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-msqm-health-analytics-online-ms": {
        "summary": "Healthcare professionals describe Fuqua's online MSQM: Health Analytics as a part-time analytics degree focused on health-data applications; praise includes Duke Medicine ties and growing health-analytics hiring, with cautions about regulatory complexity in healthcare data and less finance-recruiting density than the business-analytics track.",
        "themes": [
            {
                "label": "Health analytics focus",
                "sentiment": "positive",
                "detail": "Curriculum applies analytics to clinical, payer, and pharma datasets.",
            },
            {
                "label": "Duke Medicine ties",
                "sentiment": "positive",
                "detail": "Duke University Hospital and DCRI provide health-data context.",
            },
            {
                "label": "Flexible online format",
                "sentiment": "positive",
                "detail": "Part-time schedule suits working healthcare analysts.",
            },
            {
                "label": "Healthcare regulation",
                "sentiment": "caution",
                "detail": "HIPAA and clinical-data constraints complicate real-world projects.",
            },
            {
                "label": "Narrower recruiting",
                "sentiment": "mixed",
                "detail": "Fewer Wall Street roles than the business-analytics MSQM track.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 MSQM Health Analytics (online)",
                "url": "https://www.fuqua.duke.edu/programs/msqm-health-analytics-online",
            },
            {
                "label": "Duke Clinical Research Institute",
                "url": "https://dcri.org/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-phd-in-business-administration-phd": {
        "summary": "Doctoral students describe Fuqua's Ph.D. in Business Administration as a research-intensive program in accounting, finance, marketing, and management; praise includes close faculty mentorship and interdisciplinary Duke resources, with cautions about competitive academic job markets and a smaller faculty than large public business Ph.D. programs.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Small cohorts enable close advisor relationships across business disciplines.",
            },
            {
                "label": "Interdisciplinary Duke",
                "sentiment": "positive",
                "detail": "Health, engineering, and policy schools enrich applied business research.",
            },
            {
                "label": "Fuqua reputation",
                "sentiment": "positive",
                "detail": "Fuqua ranks among top business schools for finance and management research.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty positions are nationally competitive.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than large public business Ph.D. programs with fewer specialty tracks.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 Ph.D. Program",
                "url": "https://www.fuqua.duke.edu/programs/phd",
            },
            {
                "label": "U.S. News \u2014 Fuqua Business School",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/duke-university-fuqua-01044",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-phd-in-nursing-phd": {
        "summary": "Doctoral students describe Duke's Ph.D. in Nursing as a research degree preparing nurse scientists \u2014 U.S. News ranks Duke Nursing among top graduate nursing schools; praise includes faculty mentorship in health-services research and Duke Medicine ties, with cautions about competitive academic hiring and long dissertation timelines.",
        "themes": [
            {
                "label": "Nurse-scientist training",
                "sentiment": "positive",
                "detail": "Ph.D. prepares researchers in health-services and clinical nursing science.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Close advisor relationships with nursing and medicine faculty.",
            },
            {
                "label": "Duke Medicine ties",
                "sentiment": "positive",
                "detail": "Hospital and DCRI resources support health-services research.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track nursing faculty positions are competitive.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Doctoral programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Duke School of Nursing \u2014 PhD Program",
                "url": "https://nursing.duke.edu/academics/programs/phd",
            },
            {
                "label": "U.S. News \u2014 Duke Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/duke-university-03060",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "duke-weekend-executive-mba-ms": {
        "summary": "Working professionals describe Fuqua's Weekend Executive MBA as a part-time MBA with monthly Durham residencies and the Team Fuqua collaborative culture; praise includes strong finance/consulting outcomes and STEM designation, with cautions about balancing work and residency weekends and Durham's distance from major finance hubs.",
        "themes": [
            {
                "label": "Executive cohort",
                "sentiment": "positive",
                "detail": "Peers bring substantial work experience across industries.",
            },
            {
                "label": "Team Fuqua culture",
                "sentiment": "positive",
                "detail": "Collaborative community extends to part-time MBA students.",
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": "Fuqua reports strong placement in finance, consulting, and tech.",
            },
            {
                "label": "Residency travel",
                "sentiment": "caution",
                "detail": "Monthly on-campus residencies require time away from work and family.",
            },
            {
                "label": "Location",
                "sentiment": "mixed",
                "detail": "Durham is livable but not a major finance/consulting hub like NYC or Chicago.",
            },
        ],
        "sources": [
            {
                "label": "Fuqua \u2014 Weekend Executive MBA",
                "url": "https://www.fuqua.duke.edu/programs/weekend-executive-mba",
            },
            {
                "label": "Poets&Quants \u2014 Duke Fuqua",
                "url": "https://poetsandquants.com/schools/duke-universitys-fuqua-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
