"""Columbia University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``columbiaprof8`` migration to merge
``DEPTH_REVIEWS`` into ``columbia_profile._REVIEWS_BY_SLUG`` for 37
remaining coverable programs (47/47 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "columbia-advanced-graduate-dentistry-and-oral-sciences-ms": {
        "summary": "Students describe Mailman School's Master's in Advanced/Graduate Dentistry and Oral Sciences as public-health training at a top-ranked school \u2014 U.S. News ranks Columbia's MPH tied for No. 6 (2026); praise includes NYC health-agency access, with cautions about analytical rigor and high tuition relative to public peers.",
        "themes": [
            {
                "label": "Top public-health rank",
                "sentiment": "positive",
                "detail": "U.S. News 2026: Columbia MPH tied for No. 6 nationally.",
            },
            {
                "label": "NYC health agencies",
                "sentiment": "positive",
                "detail": "DOH, hospitals, and nonprofits provide field experience.",
            },
            {
                "label": "Analytical rigor",
                "sentiment": "positive",
                "detail": "Quantitative methods anchor public-health training.",
            },
            {
                "label": "High tuition",
                "sentiment": "caution",
                "detail": "Private-university cost exceeds most public MPH programs.",
            },
            {
                "label": "Large cohort",
                "sentiment": "mixed",
                "detail": "Students must proactively network in a sizable program.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Advanced/Graduate Dentistry and Oral Sciences",
                "url": "https://www.publichealth.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-architecture-bs": {
        "summary": "Students describe Columbia GSAPP's undergraduate architecture pathway as design-intensive training within a school historically ranked among the top U.S. architecture programs \u2014 DesignIntelligence has ranked Columbia among leading architecture schools; praise includes studio culture and NYC design firms, with cautions about demanding studio workloads and limited undergraduate architecture seats relative to peer programs.",
        "themes": [
            {
                "label": "Design studio culture",
                "sentiment": "positive",
                "detail": "Intensive studio sequences build portfolio-ready design work.",
            },
            {
                "label": "NYC design access",
                "sentiment": "positive",
                "detail": "Proximity to major architecture firms and cultural institutions.",
            },
            {
                "label": "GSAPP reputation",
                "sentiment": "positive",
                "detail": "Columbia GSAPP ranks among top U.S. architecture schools historically.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Architecture studios are time-intensive even by Columbia standards.",
            },
            {
                "label": "Selective pathway",
                "sentiment": "mixed",
                "detail": "Architecture admits a smaller cohort than general Columbia College majors.",
            },
        ],
        "sources": [
            {
                "label": "Columbia GSAPP",
                "url": "https://www.arch.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Architecture Rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-arts-mfa": {
        "summary": "Students describe Columbia School of the Arts MFA programs as intensive, studio-based graduate training in film, theatre, writing, and visual arts within a major research university in New York City; praise includes faculty practitioners and NYC industry access, with cautions about high tuition, competitive admission, and variable career outcomes across creative fields.",
        "themes": [
            {
                "label": "NYC creative industries",
                "sentiment": "positive",
                "detail": "Film, theatre, publishing, and gallery networks are steps from campus.",
            },
            {
                "label": "Practitioner faculty",
                "sentiment": "positive",
                "detail": "Working artists and writers teach studio and workshop courses.",
            },
            {
                "label": "Interdisciplinary Columbia",
                "sentiment": "positive",
                "detail": "Access to a top research university and cross-school electives.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Manhattan tuition and living expenses are among the highest nationally.",
            },
            {
                "label": "Variable career paths",
                "sentiment": "mixed",
                "detail": "Creative-field outcomes depend heavily on portfolio and networking.",
            },
        ],
        "sources": [
            {
                "label": "Columbia School of the Arts",
                "url": "https://arts.columbia.edu/",
            },
            {
                "label": "Niche \u2014 Columbia University",
                "url": "https://www.niche.com/colleges/columbia-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-biomedical-engineering-bs": {
        "summary": "Students describe Columbia's Biomedical Engineering B.S. as an interdisciplinary engineering degree bridging SEAS and CUIMC \u2014 praise includes access to NewYork-Presbyterian research and NYC biotech recruiting, with cautions about demanding math and biology prerequisites and a smaller BME cohort than large public programs.",
        "themes": [
            {
                "label": "CUIMC integration",
                "sentiment": "positive",
                "detail": "Proximity to medical campus enables translational BME research.",
            },
            {
                "label": "Interdisciplinary training",
                "sentiment": "positive",
                "detail": "Curriculum bridges engineering, biology, and clinical applications.",
            },
            {
                "label": "NYC biotech access",
                "sentiment": "positive",
                "detail": "Pharma and medtech firms recruit Columbia BME graduates.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Math, physics, and biology sequences are rigorous.",
            },
            {
                "label": "Smaller cohort",
                "sentiment": "mixed",
                "detail": "BME is smaller than at Johns Hopkins or large public programs.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Biomedical Engineering",
                "url": "https://www.bme.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Engineering Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-biomedical-medical-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Biomedical/Medical Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Biomedical/Medical Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-chemical-engineering-bs": {
        "summary": "Students describe Columbia's Chemical Engineering B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Chemical Engineering",
                "url": "https://cheme.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-chemical-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Chemical Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Chemical Engineering",
                "url": "https://cheme.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-civil-engineering-bs": {
        "summary": "Students describe Columbia's Civil Engineering B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Civil Engineering",
                "url": "https://civil.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-civil-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Civil Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Civil Engineering",
                "url": "https://civil.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-computer-engineering-bs": {
        "summary": "Students describe Columbia's Computer Engineering B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Computer Engineering",
                "url": "https://www.ee.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-computer-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Computer Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Computer Engineering",
                "url": "https://www.ee.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-computer-science-ms": {
        "summary": "Graduate students describe Columbia's M.S. in Computer Science as a rigorous, research-oriented degree within a top-20 U.S. CS program \u2014 U.S. News ranks Columbia's graduate CS #12 nationally (2025) \u2014 with strengths in machine learning, NLP, and systems and unmatched NYC tech-industry access. Common cautions are competitive admission, high Manhattan living costs, and a large program where students must proactively seek faculty mentorship.",
        "themes": [
            {
                "label": "Top CS graduate rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Columbia graduate CS #12 nationally (2025).",
            },
            {
                "label": "NYC tech access",
                "sentiment": "positive",
                "detail": "Proximity to finance, media, and startup employers in Manhattan.",
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Faculty labs span ML, NLP, robotics, and security at the Data Science Institute.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Selective MS pool with strong quantitative backgrounds expected.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Students must seek out individualized faculty advising in a sizable cohort.",
            },
        ],
        "sources": [
            {
                "label": "Columbia CS \u2014 M.S. Program",
                "url": "https://www.cs.columbia.edu/education/ms/",
            },
            {
                "label": "U.S. News \u2014 Best Computer Science Programs",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-data-analytics-ms": {
        "summary": "Students describe Columbia's analytics-oriented master's as a quantitative graduate program leveraging the Data Science Institute and Columbia Engineering; praise includes NYC finance and consulting recruiting, with cautions about self-funded tuition for terminal master's students and a fast-moving analytics job market.",
        "themes": [
            {
                "label": "Analytics & ML training",
                "sentiment": "positive",
                "detail": "Coursework emphasizes statistics, computing, and business applications.",
            },
            {
                "label": "NYC recruiting",
                "sentiment": "positive",
                "detail": "Finance and consulting firms hire Columbia quantitative graduates.",
            },
            {
                "label": "DSI resources",
                "sentiment": "positive",
                "detail": "Access to Data Science Institute faculty and research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without research assistantships.",
            },
            {
                "label": "Evolving job market",
                "sentiment": "mixed",
                "detail": "Analytics hiring cycles shift with tech and finance industry trends.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Data Science Institute",
                "url": "https://datascience.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-data-science-bs": {
        "summary": "Students describe Columbia's Data Science undergraduate major as a quantitatively rigorous program bridging statistics, computing, and domain applications \u2014 anchored by the Data Science Institute; praise includes research access and NYC industry recruiting, with cautions about demanding prerequisites and competitive grading in quantitative gateway courses.",
        "themes": [
            {
                "label": "Data Science Institute",
                "sentiment": "positive",
                "detail": "DSI faculty and research labs enrich undergraduate data-science training.",
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Curriculum spans statistics, machine learning, and computational methods.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, media, and tech firms recruit Columbia quantitative graduates.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Math and computing sequences are rigorous from the first year.",
            },
            {
                "label": "Competitive atmosphere",
                "sentiment": "mixed",
                "detail": "Popular quantitative majors can feel intense at a selective university.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Data Science Institute",
                "url": "https://datascience.columbia.edu/",
            },
            {
                "label": "Niche \u2014 Columbia University",
                "url": "https://www.niche.com/colleges/columbia-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-data-science-ms": {
        "summary": "Graduate students describe Columbia's Data Science master's as a professionally oriented program through the Data Science Institute \u2014 combining statistics, machine learning, and capstone projects with NYC employer access; praise includes industry capstones and DSI faculty, with cautions about high tuition and competition with dedicated analytics programs at peer schools.",
        "themes": [
            {
                "label": "DSI capstone projects",
                "sentiment": "positive",
                "detail": "Industry and research capstones apply ML to real datasets.",
            },
            {
                "label": "NYC employer access",
                "sentiment": "positive",
                "detail": "Finance, consulting, and tech firms recruit Columbia data graduates.",
            },
            {
                "label": "Interdisciplinary faculty",
                "sentiment": "positive",
                "detail": "DSI spans engineering, statistics, and domain sciences.",
            },
            {
                "label": "High tuition",
                "sentiment": "caution",
                "detail": "Private-university graduate tuition plus Manhattan living costs.",
            },
            {
                "label": "Peer competition",
                "sentiment": "mixed",
                "detail": "Dedicated analytics MS programs at NYU, Cornell Tech, and peer schools compete.",
            },
        ],
        "sources": [
            {
                "label": "Columbia DSI \u2014 MS in Data Science",
                "url": "https://datascience.columbia.edu/education/programs/m-s-in-data-science/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-dentistry-phd": {
        "summary": "Doctoral students describe Columbia's Doctor of Philosophy in Dentistry within Mailman School of Public Health as research-intensive training at a top-15 national university \u2014 U.S. News ranks Columbia #15 (2026); praise includes faculty mentorship and NYC research resources, with cautions about competitive funding and long time-to-degree timelines.",
        "themes": [
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Columbia's R1 status supports doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research.",
            },
            {
                "label": "NYC resources",
                "sentiment": "positive",
                "detail": "Policy, finance, and cultural institutions enrich graduate research.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across departments.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Dentistry",
                "url": "https://www.publichealth.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-economics-ms": {
        "summary": "Graduate students describe Columbia's M.A. in Economics as a quantitatively rigorous program preparing students for doctoral study or policy and finance careers \u2014 Columbia's economics department ranks among top U.S. programs; praise includes faculty research depth and NYC policy/finance access, with cautions about demanding coursework and variable Ph.D. placement for terminal master's students.",
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Core micro, macro, and econometrics at graduate level.",
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": "Columbia economics faculty lead research in trade, development, and finance.",
            },
            {
                "label": "NYC policy & finance",
                "sentiment": "positive",
                "detail": "Proximity to Wall Street, the Fed, and UN policy institutions.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Math-heavy sequences challenge students without strong quant backgrounds.",
            },
            {
                "label": "Ph.D. placement variability",
                "sentiment": "mixed",
                "detail": "Terminal MA outcomes vary between doctoral admission and industry roles.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Economics \u2014 Graduate Programs",
                "url": "https://econ.columbia.edu/graduate/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/columbia-university-2707",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Electrical, Electronics, and Communications Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-electrical-engineering-bs": {
        "summary": "Students describe Columbia's Electrical Engineering B.S. within SEAS as a quantitatively rigorous program with strengths in signals, systems, and embedded computing; praise includes research labs and NYC tech recruiting, with cautions about competitive grading and a structured engineering core.",
        "themes": [
            {
                "label": "Signals & systems depth",
                "sentiment": "positive",
                "detail": "Curriculum spans circuits, communications, and embedded systems.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Faculty labs in communications, VLSI, and control systems.",
            },
            {
                "label": "NYC tech recruiting",
                "sentiment": "positive",
                "detail": "Finance-tech and startup employers hire Columbia EE graduates.",
            },
            {
                "label": "Structured core",
                "sentiment": "caution",
                "detail": "Engineering prerequisites limit early specialization.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller EE cohort than large public engineering schools.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Electrical Engineering",
                "url": "https://www.ee.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Engineering Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-engineering-mechanics-bs": {
        "summary": "Students describe Columbia's Engineering Mechanics B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Engineering Mechanics",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-engineering-other-bs": {
        "summary": "Students describe Columbia's Engineering, Other B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Engineering, Other",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-engineering-physics-bs": {
        "summary": "Students describe Columbia's Engineering Physics B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Engineering Physics",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-engineering-physics-ms": {
        "summary": "Graduate students describe Columbia's Master's in Engineering Physics within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Engineering Physics",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-environmental-environmental-health-engineering-bs": {
        "summary": "Students describe Columbia's Environmental/Environmental Health Engineering B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Environmental/Environmental Health Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-environmental-environmental-health-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Environmental/Environmental Health Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Environmental/Environmental Health Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-finance-and-financial-management-services-ms": {
        "summary": "Students describe Columbia Business School's finance-oriented master's programs as rigorous training at a top-10 U.S. business school \u2014 U.S. News ranks CBS #8 among business schools (2026) \u2014 with unmatched Wall Street access. Praise includes value-investing heritage and NYC recruiting; cautions are high tuition, intense competition, and a finance-heavy culture.",
        "themes": [
            {
                "label": "Wall Street access",
                "sentiment": "positive",
                "detail": "Unmatched proximity to investment banks, asset managers, and hedge funds.",
            },
            {
                "label": "Value investing heritage",
                "sentiment": "positive",
                "detail": "Heilbrunn Center anchors Columbia's value-investing tradition.",
            },
            {
                "label": "Top business school rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Columbia Business School #8 nationally (2026).",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Manhattan tuition and living expenses are among the highest nationally.",
            },
            {
                "label": "Finance-heavy culture",
                "sentiment": "mixed",
                "detail": "A competitive, finance-oriented environment can feel intense.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Business School",
                "url": "https://business.columbia.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Columbia Business School",
                "url": "https://poetsandquants.com/school/columbia-business-school/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-industrial-engineering-bs": {
        "summary": "Students describe Columbia's Industrial Engineering B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across SEAS departments.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Industrial Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-industrial-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Industrial Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Industrial Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-law-phd": {
        "summary": "Legal scholars describe Columbia Law's Ph.D. in Law as an advanced research degree for candidates pursuing academic legal careers \u2014 Columbia Law ranks tied for No. 9 nationally (U.S. News 2026); praise includes faculty mentorship and NYC legal-institution access, with cautions about extremely competitive law-faculty hiring and a demanding dissertation timeline.",
        "themes": [
            {
                "label": "Legal scholarship",
                "sentiment": "positive",
                "detail": "Doctoral candidates produce dissertation-level legal research.",
            },
            {
                "label": "Top law school rank",
                "sentiment": "positive",
                "detail": "U.S. News 2026: Columbia Law tied for No. 9 nationally.",
            },
            {
                "label": "NYC legal institutions",
                "sentiment": "positive",
                "detail": "Courts, firms, and policy organizations enrich legal research.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are highly competitive.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "mixed",
                "detail": "Doctoral completion commonly spans five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Law \u2014 Graduate Legal Studies",
                "url": "https://www.law.columbia.edu/academics/graduate-legal-studies",
            },
            {
                "label": "U.S. News \u2014 Columbia Law",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/columbia-university-03011",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-mathematics-and-computer-science-bs": {
        "summary": "Students describe Columbia's Mathematics and Computer Science major within Columbia College as a quantitatively rigorous degree \u2014 Niche rates Columbia among top New York colleges for computer science; praise includes research access and NYC industry recruiting, with cautions about competitive grading.",
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Strong foundations in computing, statistics, and applied math.",
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Data Science Institute and CS faculty labs enrich study.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, media, and tech firms recruit Columbia graduates.",
            },
            {
                "label": "Competitive atmosphere",
                "sentiment": "caution",
                "detail": "Selective major with demanding coursework.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "mixed",
                "detail": "Gateway sequences can include large lectures.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Mathematics and Computer Science",
                "url": "https://www.cs.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-mechanical-engineering-bs": {
        "summary": "Students describe Columbia's Mechanical Engineering B.S. within SEAS as a rigorous engineering degree at a selective private R1 university in New York City; praise includes undergraduate research access and NYC industry recruiting, with cautions about demanding prerequisites and a smaller engineering school than large public tech universities.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs in robotics, energy, and materials.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, aerospace, and tech firms recruit Columbia engineers.",
            },
            {
                "label": "Small SEAS cohort",
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
                "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Mechanical Engineering",
                "url": "https://www.me.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Engineering Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-mechanical-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Mechanical Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Mechanical Engineering",
                "url": "https://www.me.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-medicine-phd": {
        "summary": "Doctoral students describe Columbia's Ph.D. programs in biomedical sciences through Vagelos and CUIMC as research-intensive training at a top NIH-funded medical campus; praise includes clinical and translational research access at NewYork-Presbyterian, with cautions about competitive funding and long time-to-degree timelines.",
        "themes": [
            {
                "label": "CUIMC research",
                "sentiment": "positive",
                "detail": "NIH-funded labs span basic, translational, and clinical science.",
            },
            {
                "label": "Clinical integration",
                "sentiment": "positive",
                "detail": "NewYork-Presbyterian provides patient-centered research context.",
            },
            {
                "label": "NYC biomedical ecosystem",
                "sentiment": "positive",
                "detail": "Pharma, biotech, and hospital networks enrich doctoral training.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships and fellowships are competitive.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Biomedical Ph.D. timelines commonly span five to seven years.",
            },
        ],
        "sources": [
            {
                "label": "Vagelos College \u2014 Graduate Programs",
                "url": "https://www.vagelos.columbia.edu/education/phd-programs",
            },
            {
                "label": "Columbia Irving Medical Center",
                "url": "https://www.cuimc.columbia.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-mining-and-mineral-engineering-ms": {
        "summary": "Graduate students describe Columbia's Master's in Mining and Mineral Engineering within SEAS as a professional coursework degree in New York City; praise includes NYC industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "SEAS engineering reputation",
                "sentiment": "positive",
                "detail": "Columbia Engineering ranks among leading private engineering schools.",
            },
            {
                "label": "NYC industry access",
                "sentiment": "positive",
                "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers.",
            },
            {
                "label": "Research & coursework",
                "sentiment": "positive",
                "detail": "Graduate programs combine advanced coursework with lab research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship public engineering schools at peer universities.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Mining and Mineral Engineering",
                "url": "https://www.engineering.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-nursing-msn": {
        "summary": "Students describe Columbia Nursing's Master's Direct Entry (MDE) program as an accelerated path to RN licensure and an MSN for career changers \u2014 U.S. News ranks Columbia's graduate nursing programs among the top nationally; praise includes clinical training at NewYork-Presbyterian / CUIMC and a Manhattan healthcare network, with cautions about an intensive accelerated pace and high program cost.",
        "themes": [
            {
                "label": "Accelerated MDE format",
                "sentiment": "positive",
                "detail": "Career changers earn RN licensure and an MSN in a compressed timeline.",
            },
            {
                "label": "CUIMC clinical training",
                "sentiment": "positive",
                "detail": "Rotations at NewYork-Presbyterian and NYC health systems.",
            },
            {
                "label": "Top nursing reputation",
                "sentiment": "positive",
                "detail": "Columbia Nursing ranks among leading graduate nursing programs nationally.",
            },
            {
                "label": "Intensive pace",
                "sentiment": "caution",
                "detail": "Accelerated curriculum demands sustained clinical and coursework load.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Private-university tuition plus Manhattan living expenses.",
            },
        ],
        "sources": [
            {
                "label": "Columbia Nursing \u2014 Master's Direct Entry",
                "url": "https://www.nursing.columbia.edu/academics/masters-direct-entry",
            },
            {
                "label": "U.S. News \u2014 Columbia Nursing",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/columbia-university-03011",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-bs": {
        "summary": "Students describe Columbia Nursing's Bachelor's in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as training at a top graduate nursing school with clinical rotations at NewYork-Presbyterian / CUIMC; praise includes NYC healthcare access, with cautions about intensive clinical workloads and high private-university cost.",
        "themes": [
            {
                "label": "CUIMC clinical training",
                "sentiment": "positive",
                "detail": "Rotations at NewYork-Presbyterian and NYC health systems.",
            },
            {
                "label": "Top nursing reputation",
                "sentiment": "positive",
                "detail": "Columbia Nursing ranks among leading graduate programs.",
            },
            {
                "label": "NYC healthcare network",
                "sentiment": "positive",
                "detail": "Diverse clinical sites across Manhattan and the metro area.",
            },
            {
                "label": "Clinical intensity",
                "sentiment": "caution",
                "detail": "Nursing programs combine demanding coursework and clinical hours.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Private-university tuition plus Manhattan living expenses.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://www.nursing.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/columbia-university-03011",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "columbia-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": {
        "summary": "Students describe Columbia Nursing's Doctor of Philosophy in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as training at a top graduate nursing school with clinical rotations at NewYork-Presbyterian / CUIMC; praise includes NYC healthcare access, with cautions about intensive clinical workloads and high private-university cost.",
        "themes": [
            {
                "label": "CUIMC clinical training",
                "sentiment": "positive",
                "detail": "Rotations at NewYork-Presbyterian and NYC health systems.",
            },
            {
                "label": "Top nursing reputation",
                "sentiment": "positive",
                "detail": "Columbia Nursing ranks among leading graduate programs.",
            },
            {
                "label": "NYC healthcare network",
                "sentiment": "positive",
                "detail": "Diverse clinical sites across Manhattan and the metro area.",
            },
            {
                "label": "Clinical intensity",
                "sentiment": "caution",
                "detail": "Nursing programs combine demanding coursework and clinical hours.",
            },
            {
                "label": "High cost",
                "sentiment": "caution",
                "detail": "Private-university tuition plus Manhattan living expenses.",
            },
        ],
        "sources": [
            {
                "label": "Columbia \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://www.nursing.columbia.edu/",
            },
            {
                "label": "U.S. News \u2014 Columbia University",
                "url": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/columbia-university-03011",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
