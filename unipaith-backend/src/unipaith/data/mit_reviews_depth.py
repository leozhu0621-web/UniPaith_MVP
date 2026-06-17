"""Massachusetts Institute of Technology external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``mitprof4`` migration to merge
``DEPTH_REVIEWS`` into ``mit_profile._REVIEWS_BY_SLUG`` for 16 remaining
coverable programs (23/23 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "mit-architecture-bs": {
        "summary": (
            "Students and architecture guides describe MIT's undergraduate "
            "architecture major (Course 4-B) within the School of Architecture "
            "and Planning as a design-and-technology program at a globally "
            "ranked school — QS places MIT No. 2 in Architecture & Built "
            "Environment — praising studio culture, computation labs, and "
            "interdisciplinary ties to engineering. Common cautions are long "
            "studio hours, that the B.S. in Architecture Studies is a "
            "pre-professional degree requiring further study for licensure, "
            "and the overall MIT workload."
        ),
        "themes": [
            {
                "label": "Global architecture standing",
                "sentiment": "positive",
                "detail": (
                    "QS ranks MIT among the top architecture programs worldwide."
                ),
            },
            {
                "label": "Design & technology integration",
                "sentiment": "positive",
                "detail": (
                    "Studios combine digital fabrication, environmental systems, "
                    "and computational design."
                ),
            },
            {
                "label": "Interdisciplinary MIT ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Architecture students cross-register with engineering and "
                    "urban-planning offerings."
                ),
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": (
                    "Long studio hours and intensive crit schedules are recurring "
                    "student themes."
                ),
            },
            {
                "label": "Pre-professional path",
                "sentiment": "mixed",
                "detail": (
                    "The undergraduate degree is not the NAAB-accredited "
                    "professional path; the M.Arch. follows for licensure."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT SAP — Undergraduate degrees",
                "url": (
                    "https://sap.mit.edu/education/"
                    "undergraduate-degrees-and-requirements"
                ),
            },
            {
                "label": "QS — Architecture & Built Environment",
                "url": (
                    "https://www.topuniversities.com/university-subject-rankings/"
                    "architecture-built-environment"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-be-bs": {
        "summary": (
            "Students and guides describe MIT's Course 20 (Biological Engineering) "
            "as a rigorous undergraduate major bridging molecular biology and "
            "quantitative engineering — U.S. News ranks MIT among the top U.S. "
            "bioengineering programs — praising research lab access and the "
            "department's synthetic-biology focus. Common cautions are the heavy "
            "shared MIT science core, limited class size in upper-level electives, "
            "and that pre-med students must plan requirements carefully."
        ),
        "themes": [
            {
                "label": "Bio-engineering bridge",
                "sentiment": "positive",
                "detail": (
                    "Course 20 integrates biology, chemistry, and engineering design."
                ),
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": (
                    "UROP and department labs offer term-time research from the "
                    "first year."
                ),
            },
            {
                "label": "Top bioengineering rank",
                "sentiment": "positive",
                "detail": (
                    "MIT bioengineering regularly appears in top national rankings."
                ),
            },
            {
                "label": "Shared science core",
                "sentiment": "caution",
                "detail": (
                    "Physics, math, and chemistry requirements dominate early terms."
                ),
            },
            {
                "label": "Pre-med coordination",
                "sentiment": "mixed",
                "detail": (
                    "Students note careful planning is needed to satisfy both BE "
                    "and medical-school prerequisites."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT BE — Undergraduate program",
                "url": "https://be.mit.edu/undergraduate/",
            },
            {
                "label": "U.S. News — Bioengineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "bioengineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-cee-bs": {
        "summary": (
            "Students and guides describe MIT's Course 1 (Civil & Environmental "
            "Engineering) as a top-ranked undergraduate program combining "
            "infrastructure, environmental systems, and data-driven design — "
            "U.S. News places MIT No. 1 among U.S. civil engineering programs — "
            "praising field projects, climate-focused research, and the 1.ENG "
            "flexible engineering degree. Common cautions are the demanding "
            "quantitative core and that the major is smaller than EECS or "
            "mechanical engineering."
        ),
        "themes": [
            {
                "label": "National civil engineering leadership",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT No. 1 in civil engineering among U.S. "
                    "graduate programs, reflecting department strength."
                ),
            },
            {
                "label": "Climate & infrastructure focus",
                "sentiment": "positive",
                "detail": (
                    "Coursework spans sustainable cities, water systems, and "
                    "structural design."
                ),
            },
            {
                "label": "Project-based learning",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join design projects and research on real "
                    "infrastructure challenges."
                ),
            },
            {
                "label": "Quantitative intensity",
                "sentiment": "caution",
                "detail": (
                    "Shared MIT math and physics requirements are demanding."
                ),
            },
            {
                "label": "Smaller cohort",
                "sentiment": "mixed",
                "detail": (
                    "Fewer peers than in Course 6 or Course 2, though class "
                    "sizes stay small."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT CEE — Undergraduate program",
                "url": "https://cee.mit.edu/education/undergraduate-program/",
            },
            {
                "label": "U.S. News — Civil engineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "civil-engineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-cheme-bs": {
        "summary": (
            "Students and guides consistently rank MIT's Course 10 (Chemical "
            "Engineering) among the strongest undergraduate chemical-engineering "
            "programs in the United States — U.S. News places MIT No. 1 — "
            "praising its quantitative thermodynamics and transport core, "
            "biotechnology electives, and pipeline to pharmaceuticals and energy. "
            "Common cautions are the fast pace of problem sets, limited elective "
            "flexibility in the core years, and that the major is more "
            "theory-intensive than at some peer programs."
        ),
        "themes": [
            {
                "label": "National program leadership",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT No. 1 in chemical engineering."
                ),
            },
            {
                "label": "Quantitative foundations",
                "sentiment": "positive",
                "detail": (
                    "Thermodynamics, transport, and reaction engineering form a "
                    "rigorous core."
                ),
            },
            {
                "label": "Industry & grad-school paths",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter energy, biotech, materials, and Ph.D. programs."
                ),
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": (
                    "Students describe intense problem sets and lab schedules."
                ),
            },
            {
                "label": "Core rigidity",
                "sentiment": "mixed",
                "detail": (
                    "Required coursework leaves fewer free electives than some "
                    "peer majors in early years."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT ChemE — Undergraduate program",
                "url": "https://cheme.mit.edu/education/undergraduate-program/",
            },
            {
                "label": "U.S. News — Chemical engineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "chemical-engineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-cs-6-3-bs": {
        "summary": (
            "Students and college guides rank MIT's Course 6-3 (Computer Science "
            "and Engineering) among the top undergraduate CS programs in the "
            "world — U.S. News placed MIT No. 1 in undergraduate computer "
            "science for 2025–26 — praising CSAIL research access, algorithms "
            "and systems depth, and strong placement into technology and finance. "
            "Common cautions are the famously low admit rate, intense problem-set "
            "pace, and competition for popular upper-level electives."
        ),
        "themes": [
            {
                "label": "National CS leadership",
                "sentiment": "positive",
                "detail": (
                    "U.S. News No. 1 undergraduate computer science program "
                    "(2025–26)."
                ),
            },
            {
                "label": "CSAIL & research access",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates join labs across CSAIL and related institutes."
                ),
            },
            {
                "label": "Career outcomes",
                "sentiment": "positive",
                "detail": (
                    "Graduates feed top technology, quantitative finance, and "
                    "graduate programs."
                ),
            },
            {
                "label": "Selectivity & pace",
                "sentiment": "caution",
                "detail": (
                    "Roughly 4–5% undergraduate admit rate and a demanding workload."
                ),
            },
            {
                "label": "Elective competition",
                "sentiment": "mixed",
                "detail": (
                    "Popular AI and systems courses can fill quickly."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT EECS — Course 6-3",
                "url": (
                    "https://www.eecs.mit.edu/academics/undergraduate-programs/"
                    "course-6-3-computer-science-and-engineering/"
                ),
            },
            {
                "label": "MIT News — U.S. News 2025–26 rankings",
                "url": (
                    "https://news.mit.edu/2025/"
                    "mit-named-no-2-university-us-news-2025-26-0923"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-cs-econ-data-bs": {
        "summary": (
            "Students and guides describe MIT's Course 6-14 (Computer Science, "
            "Economics, and Data Science) as a newer interdisciplinary major "
            "blending EECS, economics, and statistics — launched through the "
            "MIT Schwarzman College of Computing — praising its data-economics "
            "curriculum and access to both CSAIL and the economics department. "
            "Common cautions are that the major is still establishing its cohort "
            "size, requirements span three departments, and outcomes overlap "
            "with Course 6-3 and Course 14."
        ),
        "themes": [
            {
                "label": "Interdisciplinary data economics",
                "sentiment": "positive",
                "detail": (
                    "Combines computer science, econometrics, and data-science "
                    "methods in one degree."
                ),
            },
            {
                "label": "College of Computing ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Students access computing-college courses and cross-department "
                    "faculty."
                ),
            },
            {
                "label": "Industry relevance",
                "sentiment": "positive",
                "detail": (
                    "Graduates target tech policy, quantitative finance, and "
                    "data-science roles."
                ),
            },
            {
                "label": "Newer major",
                "sentiment": "mixed",
                "detail": (
                    "Course 6-14 is newer and less established than Course 6-3."
                ),
            },
            {
                "label": "Cross-department planning",
                "sentiment": "caution",
                "detail": (
                    "Students coordinate requirements across EECS, economics, "
                    "and IDSS."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT EECS — Course 6-14",
                "url": (
                    "https://www.eecs.mit.edu/academics/undergraduate-programs/"
                    "course-6-14-computer-science-economics-and-data-science/"
                ),
            },
            {
                "label": "MIT Schwarzman College of Computing",
                "url": "https://computing.mit.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-cse-phd": {
        "summary": (
            "Doctoral students and guides describe MIT's Ph.D. in Computational "
            "Science and Engineering through the Center for Computational Science "
            "and Engineering as an interdisciplinary research degree bridging "
            "numerical methods, HPC, and domain applications across MIT "
            "departments — praising CCSE's cross-school faculty and access to "
            "MIT's computing infrastructure. Common cautions are the competitive "
            "admission pool, that students must secure a research home in a "
            "partner department, and the academic job market for computational "
            "science faculty positions."
        ),
        "themes": [
            {
                "label": "Interdisciplinary CSE research",
                "sentiment": "positive",
                "detail": (
                    "CCSE spans numerical analysis, optimization, and scientific "
                    "computing across domains."
                ),
            },
            {
                "label": "Cross-department placement",
                "sentiment": "positive",
                "detail": (
                    "Doctoral students affiliate with engineering, science, or "
                    "IDSS research groups."
                ),
            },
            {
                "label": "HPC & methods depth",
                "sentiment": "positive",
                "detail": (
                    "Training in algorithms, simulation, and data-driven modeling "
                    "at scale."
                ),
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": (
                    "MIT doctoral programs have highly selective admission pools."
                ),
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": (
                    "Tenure-track computational-science faculty positions are "
                    "nationally competitive."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT CCSE — Graduate programs",
                "url": "https://ccse.mit.edu/education/graduate/",
            },
            {
                "label": "MIT Schwarzman College of Computing",
                "url": "https://computing.mit.edu/academics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-dmse-bs": {
        "summary": (
            "Students and guides describe MIT's Course 3 (Materials Science & "
            "Engineering) as a top-ranked undergraduate program connecting "
            "structure, properties, and processing of materials — U.S. News "
            "places MIT No. 1 among U.S. materials-engineering programs — "
            "praising lab-intensive coursework and ties to energy, electronics, "
            "and biomaterials research. Common cautions are the quantitative "
            "physics and chemistry prerequisites and that the major is smaller "
            "than EECS or mechanical engineering."
        ),
        "themes": [
            {
                "label": "National materials leadership",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT No. 1 in materials engineering."
                ),
            },
            {
                "label": "Lab-intensive training",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates work in characterization and processing labs."
                ),
            },
            {
                "label": "Research & industry paths",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter semiconductors, energy storage, and Ph.D. "
                    "programs."
                ),
            },
            {
                "label": "Prerequisite intensity",
                "sentiment": "caution",
                "detail": (
                    "Strong physics and chemistry foundations are required."
                ),
            },
            {
                "label": "Smaller cohort",
                "sentiment": "mixed",
                "detail": (
                    "Course 3 is a smaller major with close faculty access."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT DMSE — Undergraduate program",
                "url": "https://dmse.mit.edu/education/undergraduate/",
            },
            {
                "label": "U.S. News — Materials engineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "materials-engineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-economics-phd": {
        "summary": (
            "Doctoral students and economics guides consistently rank MIT's "
            "economics Ph.D. among the world's most prestigious — the department "
            "is perennially top-ranked for faculty research and graduate "
            "placement — praising its micro/metrics core, access to leading "
            "faculty, and placement into academia, central banks, and tech "
            "economics. Common cautions are the highly competitive admission "
            "process, the mathematical intensity of coursework, and that the "
            "academic job market for economics faculty remains tight."
        ),
        "themes": [
            {
                "label": "Global research prestige",
                "sentiment": "positive",
                "detail": (
                    "MIT economics ranks among the top departments worldwide for "
                    "faculty research."
                ),
            },
            {
                "label": "Micro & metrics core",
                "sentiment": "positive",
                "detail": (
                    "Doctoral training emphasizes microeconomic theory and "
                    "econometrics."
                ),
            },
            {
                "label": "Placement breadth",
                "sentiment": "positive",
                "detail": (
                    "Graduates enter academia, the Federal Reserve, consulting, "
                    "and tech policy."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Admission is highly competitive with a small incoming cohort."
                ),
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": (
                    "Tenure-track economics faculty positions are nationally "
                    "competitive."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT Department of Economics — Graduate",
                "url": "https://economics.mit.edu/graduate",
            },
            {
                "label": "MIT News — U.S. News 2025–26 rankings",
                "url": (
                    "https://news.mit.edu/2025/"
                    "mit-named-no-2-university-us-news-2025-26-0923"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-eecs-phd": {
        "summary": (
            "Doctoral students and guides consistently rank MIT's EECS Ph.D. "
            "among the world's leading computer-science and electrical-engineering "
            "programs — U.S. News places MIT No. 1 in graduate computer science — "
            "praising CSAIL and related lab access, fully funded assistantships, "
            "and placement into academia and top industry labs. Common cautions are "
            "the competitive admission pool, that students must find a faculty "
            "advisor match, and the demanding pace of doctoral research."
        ),
        "themes": [
            {
                "label": "Global EECS leadership",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT No. 1 in graduate computer science."
                ),
            },
            {
                "label": "CSAIL & lab ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Doctoral students join CSAIL, LIDS, and related research "
                    "groups."
                ),
            },
            {
                "label": "Fully funded",
                "sentiment": "positive",
                "detail": (
                    "Admitted Ph.D. students receive research assistantships covering "
                    "tuition and stipend."
                ),
            },
            {
                "label": "Advisor matching",
                "sentiment": "caution",
                "detail": (
                    "Students must secure a faculty advisor in a competitive "
                    "research group."
                ),
            },
            {
                "label": "Research pace",
                "sentiment": "caution",
                "detail": (
                    "Doctoral students describe a demanding research and "
                    "publication environment."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT EECS — Graduate program",
                "url": (
                    "https://www.eecs.mit.edu/academics-admissions/"
                    "graduate-program-admissions/"
                ),
            },
            {
                "label": "U.S. News — Computer science rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-science-schools/"
                    "computer-science-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-finance-bs": {
        "summary": (
            "Students and guides describe MIT Sloan's Course 15-3 (Finance) as the "
            "quantitative finance track within MIT's undergraduate management "
            "major — U.S. News ranked MIT No. 1 among undergraduate business "
            "programs for 2025–26 — praising its markets, corporate finance, and "
            "analytics coursework alongside MIT's math core. Common cautions are "
            "that it is not a standalone undergraduate business school, career "
            "paths often require graduate study for general-management roles, and "
            "the overall MIT workload is intense."
        ),
        "themes": [
            {
                "label": "Undergraduate business ranking",
                "sentiment": "positive",
                "detail": (
                    "U.S. News No. 1 undergraduate business program (2025–26)."
                ),
            },
            {
                "label": "Quantitative finance training",
                "sentiment": "positive",
                "detail": (
                    "Course 15-3 pairs corporate finance and markets with MIT's "
                    "quantitative core."
                ),
            },
            {
                "label": "Sloan ecosystem access",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates access Sloan faculty and entrepreneurship "
                    "resources."
                ),
            },
            {
                "label": "Not a standalone B-school",
                "sentiment": "mixed",
                "detail": (
                    "Finance is a concentration within Course 15, not a separate "
                    "undergraduate college."
                ),
            },
            {
                "label": "Intensity",
                "sentiment": "caution",
                "detail": (
                    "Students report a demanding pace shared across all MIT majors."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT Sloan — Course 15-3 Finance",
                "url": "https://mitsloan.mit.edu/undergraduate/course-15-3",
            },
            {
                "label": "MIT News — U.S. News 2025–26 rankings",
                "url": (
                    "https://news.mit.edu/2025/"
                    "mit-named-no-2-university-us-news-2025-26-0923"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-math-cs-bs": {
        "summary": (
            "Students and guides describe MIT's Course 18-C (Mathematics with "
            "Computer Science) as a rigorous joint major blending pure and applied "
            "mathematics with computer-science depth — MIT's mathematics department "
            "is perennially ranked among the world's best — praising its theory "
            "foundations and pipeline to graduate study in CS and math. Common "
            "cautions are the heavy proof-based coursework, overlap with Course "
            "6-3 for software careers, and that the major requires careful "
            "scheduling across two departments."
        ),
        "themes": [
            {
                "label": "Math & CS integration",
                "sentiment": "positive",
                "detail": (
                    "Combines rigorous mathematics with computer-science "
                    "coursework."
                ),
            },
            {
                "label": "Theory foundations",
                "sentiment": "positive",
                "detail": (
                    "Proof-based analysis and algorithms training support graduate "
                    "study."
                ),
            },
            {
                "label": "Graduate-school pipeline",
                "sentiment": "positive",
                "detail": (
                    "A common path for students aiming at CS or math Ph.D. programs."
                ),
            },
            {
                "label": "Proof intensity",
                "sentiment": "caution",
                "detail": (
                    "Real analysis and abstract algebra requirements are demanding."
                ),
            },
            {
                "label": "Overlap with Course 6-3",
                "sentiment": "mixed",
                "detail": (
                    "Students note similar industry outcomes are possible through "
                    "Course 6-3 with math electives."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT Mathematics — Undergraduate degrees",
                "url": "https://math.mit.edu/academics/undergrad/degree.php",
            },
            {
                "label": "Niche — Massachusetts Institute of Technology",
                "url": (
                    "https://www.niche.com/colleges/"
                    "massachusetts-institute-of-technology/"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-meche-bs": {
        "summary": (
            "Students and guides consistently rank MIT's Course 2 (Mechanical "
            "Engineering) among the top undergraduate mechanical-engineering "
            "programs in the United States — U.S. News places MIT No. 1 — "
            "praising its design-and-build culture, robotics and energy "
            "electives, and 2.007 design competition. Common cautions are the "
            "demanding quantitative core, long lab hours, and that the major is "
            "broad rather than narrowly specialized."
        ),
        "themes": [
            {
                "label": "National MechE leadership",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT No. 1 in mechanical engineering."
                ),
            },
            {
                "label": "Design & build culture",
                "sentiment": "positive",
                "detail": (
                    "2.007 and project-based courses emphasize hands-on design."
                ),
            },
            {
                "label": "Robotics & energy breadth",
                "sentiment": "positive",
                "detail": (
                    "Electives span robotics, thermodynamics, and sustainable energy."
                ),
            },
            {
                "label": "Lab workload",
                "sentiment": "caution",
                "detail": (
                    "Students describe long hours in design labs and project courses."
                ),
            },
            {
                "label": "Broad curriculum",
                "sentiment": "mixed",
                "detail": (
                    "Course 2 covers many subfields rather than a single narrow track."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT MechE — Undergraduate program",
                "url": "https://meche.mit.edu/education/undergraduate/",
            },
            {
                "label": "U.S. News — Mechanical engineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "mechanical-engineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-meche-phd": {
        "summary": (
            "Doctoral students and guides rank MIT's mechanical-engineering Ph.D. "
            "among the world's leading programs — U.S. News places MIT No. 1 in "
            "graduate mechanical engineering — praising research in robotics, "
            "design, energy, and biomechanics with fully funded assistantships. "
            "Common cautions are the competitive admission process, advisor-matching "
            "requirements, and that the academic faculty job market is tight."
        ),
        "themes": [
            {
                "label": "Global MechE research",
                "sentiment": "positive",
                "detail": (
                    "U.S. News ranks MIT No. 1 in graduate mechanical engineering."
                ),
            },
            {
                "label": "Robotics & design labs",
                "sentiment": "positive",
                "detail": (
                    "Doctoral students join leading robotics, design, and energy "
                    "research groups."
                ),
            },
            {
                "label": "Fully funded",
                "sentiment": "positive",
                "detail": (
                    "Admitted Ph.D. students receive research assistantships."
                ),
            },
            {
                "label": "Advisor matching",
                "sentiment": "caution",
                "detail": (
                    "Students must secure a faculty advisor in a competitive lab."
                ),
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": (
                    "Tenure-track mechanical-engineering faculty positions are "
                    "competitive."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT MechE — Ph.D. program",
                "url": "https://meche.mit.edu/education/graduate/phd",
            },
            {
                "label": "U.S. News — Mechanical engineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "mechanical-engineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-nse-bs": {
        "summary": (
            "Students and guides describe MIT's Course 22 (Nuclear Science & "
            "Engineering) as a distinctive undergraduate major covering fission, "
            "fusion, and radiation science — U.S. News places MIT among the top "
            "U.S. nuclear-engineering programs — praising its reactor technology "
            "coursework and ties to MIT's Nuclear Reactor Laboratory. Common "
            "cautions are the niche hiring market outside energy and national "
            "labs, the specialized physics prerequisites, and that the major is "
            "one of MIT's smallest."
        ),
        "themes": [
            {
                "label": "Nuclear engineering depth",
                "sentiment": "positive",
                "detail": (
                    "Coursework spans reactor physics, fusion, and radiation "
                    "applications."
                ),
            },
            {
                "label": "Reactor laboratory access",
                "sentiment": "positive",
                "detail": (
                    "Undergraduates can engage with MIT's on-campus research reactor."
                ),
            },
            {
                "label": "Top program rank",
                "sentiment": "positive",
                "detail": (
                    "MIT nuclear engineering ranks among the top U.S. programs."
                ),
            },
            {
                "label": "Niche career market",
                "sentiment": "caution",
                "detail": (
                    "Hiring concentrates in energy, defense, and national laboratories."
                ),
            },
            {
                "label": "Small cohort",
                "sentiment": "mixed",
                "detail": (
                    "Course 22 is one of MIT's smallest majors with close faculty "
                    "mentoring."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT NSE — Undergraduate program",
                "url": "https://nse.mit.edu/education/undergraduate-program/",
            },
            {
                "label": "U.S. News — Nuclear engineering rankings",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-engineering-schools/"
                    "nuclear-engineering-rankings"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "mit-sloan-fellows-mba": {
        "summary": (
            "Students and executive-education guides describe MIT Sloan's Fellows "
            "MBA as a mid-career, one-year full-time MBA for experienced leaders — "
            "distinct from the two-year MBA — praising its tight cohort of "
            "seasoned professionals, Sloan analytics and leadership curriculum, "
            "and MIT innovation ecosystem access. Common cautions are the high "
            "tuition for a one-year program, that applicants need roughly 10+ years "
            "of work experience, and that the accelerated pace is demanding."
        ),
        "themes": [
            {
                "label": "Mid-career cohort",
                "sentiment": "positive",
                "detail": (
                    "Fellows enter with substantial professional experience, "
                    "creating a peer network of leaders."
                ),
            },
            {
                "label": "One-year accelerated MBA",
                "sentiment": "positive",
                "detail": (
                    "A full-time Sloan MBA compressed into twelve months for "
                    "experienced managers."
                ),
            },
            {
                "label": "MIT innovation access",
                "sentiment": "positive",
                "detail": (
                    "Fellows cross-register across MIT and access entrepreneurship "
                    "resources."
                ),
            },
            {
                "label": "Experience requirement",
                "sentiment": "caution",
                "detail": (
                    "The program targets mid-career professionals with roughly "
                    "a decade of work experience."
                ),
            },
            {
                "label": "Cost & pace",
                "sentiment": "caution",
                "detail": (
                    "One-year tuition and living expenses in Cambridge are "
                    "substantial; the schedule is intense."
                ),
            },
        ],
        "sources": [
            {
                "label": "MIT Sloan — Sloan Fellows MBA",
                "url": (
                    "https://mitsloan.mit.edu/sloan-fellows-mba-program-admissions/"
                    "admissions/about-program"
                ),
            },
            {
                "label": "Poets&Quants — Sloan Fellows program overview",
                "url": (
                    "https://poetsandquants.com/2020/01/06/"
                    "meet-mits-sloan-fellows-a-one-year-mba-for-seasoned-leaders/"
                ),
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
