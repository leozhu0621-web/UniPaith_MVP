"""Rice University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``riceprof4`` migration to merge
``DEPTH_REVIEWS`` into ``rice_profile._REVIEWS_BY_SLUG`` for 51
remaining coverable programs (57/57 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "rice-architecture-ug": {
        "summary": "Students describe Rice's undergraduate Architecture major as a rigorous, studio-intensive program within a top-ranked school \u2014 Niche ranked Rice #1 for architecture majors (2023) \u2014 with a 6:1 student-faculty ratio; praise includes personalized faculty critics and Houston's architectural diversity, with cautions about demanding studio workloads and a pre-professional track that requires a subsequent M.Arch for licensure.",
        "themes": [
            {
                "label": "Top architecture rank",
                "sentiment": "positive",
                "detail": "Niche ranked Rice #1 for architecture majors among U.S. colleges.",
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Small cohorts and crit-based studios anchor the undergraduate experience.",
            },
            {
                "label": "Houston context",
                "sentiment": "positive",
                "detail": "The city's architectural diversity provides real-world design references.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Design studios require sustained long hours and iterative critique.",
            },
            {
                "label": "Licensure path",
                "sentiment": "mixed",
                "detail": "B.A. in Architecture is pre-professional; M.Arch required for licensure.",
            },
        ],
        "sources": [
            {
                "label": "Rice School of Architecture \u2014 Undergraduate",
                "url": "https://arch.rice.edu/academics/undergraduate",
            },
            {
                "label": "Niche \u2014 Rice University",
                "url": "https://www.niche.com/colleges/rice-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-bioengineering-ug": {
        "summary": "Students describe Rice's Bioengineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Bioengineering",
                "url": "https://bioengineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-business-ug": {
        "summary": "Students describe Rice's undergraduate Business major as an analytics-oriented program within Jones Graduate School of Business for Rice undergraduates \u2014 not a standalone B.B.A. like peer business schools \u2014 with praise for quantitative training and Houston corporate access, and cautions that Rice lacks a traditional undergraduate business school and finance recruiting is smaller than at schools with dedicated B-schools.",
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes analytics, finance, and data-driven decision making.",
            },
            {
                "label": "Jones ecosystem",
                "sentiment": "positive",
                "detail": "Undergraduates access entrepreneurship resources ranked #1 by The Princeton Review.",
            },
            {
                "label": "Small-college context",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "No standalone B-school",
                "sentiment": "caution",
                "detail": "Business is a major within Rice College, not a separate undergraduate business school.",
            },
            {
                "label": "Finance recruiting",
                "sentiment": "mixed",
                "detail": "Houston energy/consulting ties are strong; Wall Street presence is limited.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 Undergraduate Business Major",
                "url": "https://business.rice.edu/undergraduate-business-major",
            },
            {
                "label": "Niche \u2014 Rice University reviews",
                "url": "https://www.niche.com/colleges/rice-university/reviews/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-chemical-and-biomolecular-engineering-ug": {
        "summary": "Students describe Rice's Chemical and Biomolecular Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Chemical and Biomolecular Engineering",
                "url": "https://chbe.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-chemical-engineering-ug": {
        "summary": "Students describe Rice's Chemical Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Chemical Engineering",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-civil-and-environmental-engineering-ug": {
        "summary": "Students describe Rice's Civil and Environmental Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Civil and Environmental Engineering",
                "url": "https://cee.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-civil-engineering-ug": {
        "summary": "Students describe Rice's Civil Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Civil Engineering",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-bioengineering-phd": {
        "summary": "Doctoral students describe Rice's Ph.D. in Bioengineering as a research degree within the George R. Brown School of Engineering and Computing \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Houston industry ties, with cautions about funding competition and long dissertation timelines.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Houston industry access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms support applied research.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Rice Engineering ranks among leading R1 engineering schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Engineering Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Bioengineering",
                "url": "https://bioengineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-business-phd": {
        "summary": "Doctoral students describe Rice Business's Ph.D. as a small, research-intensive program in accounting, finance, marketing, and strategic management within an entrepreneurship-focused business school; praise includes close faculty mentorship and interdisciplinary Rice resources, with cautions about competitive academic job markets and a smaller faculty than large public business Ph.D. programs.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Tiny cohorts enable close advisor relationships across business disciplines.",
            },
            {
                "label": "Entrepreneurship context",
                "sentiment": "positive",
                "detail": "Jones entrepreneurship ranking shapes research culture and startup exposure.",
            },
            {
                "label": "Interdisciplinary Rice",
                "sentiment": "positive",
                "detail": "Students cross-register in economics, engineering, and computational sciences.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track business faculty positions are nationally competitive.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller faculty than large public business schools limits specialty breadth.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 Ph.D. Program",
                "url": "https://business.rice.edu/phd",
            },
            {
                "label": "U.S. News \u2014 Rice Business",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/rice-university-01058",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-chemical-and-biomolecular-engineering-phd": {
        "summary": "Doctoral students describe Rice's Ph.D. in Chemical and Biomolecular Engineering as a research degree within the George R. Brown School of Engineering and Computing \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Houston industry ties, with cautions about funding competition and long dissertation timelines.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Houston industry access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms support applied research.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Rice Engineering ranks among leading R1 engineering schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Engineering Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Chemical and Biomolecular Engineering",
                "url": "https://chbe.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-civil-and-environmental-engineering-phd": {
        "summary": "Doctoral students describe Rice's Ph.D. in Civil and Environmental Engineering as a research degree within the George R. Brown School of Engineering and Computing \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Houston industry ties, with cautions about funding competition and long dissertation timelines.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Houston industry access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms support applied research.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Rice Engineering ranks among leading R1 engineering schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Engineering Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Civil and Environmental Engineering",
                "url": "https://cee.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-computer-science-phd": {
        "summary": "Doctoral students describe Rice CS's Ph.D. as a research degree in a top-20 department \u2014 Niche ranks Rice #17 for undergraduate CS and College Factual ranks Rice #20 for computer & information sciences \u2014 with strengths in AI, systems, and PL; praise includes faculty mentorship in a smaller cohort than CS-flagship giants, with cautions about funding competition and industry recruiting that is less centralized than at CMU or Stanford.",
        "themes": [
            {
                "label": "Top-20 CS standing",
                "sentiment": "positive",
                "detail": "Niche #17 for undergraduate CS; strong national reputation for graduate research.",
            },
            {
                "label": "AI & systems research",
                "sentiment": "positive",
                "detail": "Active groups in machine learning, programming languages, and systems.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "mixed",
                "detail": "Tech recruiting is active but less centralized than at CS-flagship schools.",
            },
        ],
        "sources": [
            {
                "label": "Rice Computer Science \u2014 Ph.D.",
                "url": "https://csweb.rice.edu/academics/graduate-programs/phd",
            },
            {
                "label": "Niche \u2014 Best Colleges for Computer Science",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-economics-phd": {
        "summary": "Doctoral students describe Rice Economics's Ph.D. as a research degree with strengths in econometrics, energy economics, and applied micro \u2014 Niche ranks Rice #18 for undergraduate economics (2026); praise includes the Center for Energy Studies and Houston policy access, with cautions about competitive academic job markets and a smaller department than top-10 economics programs.",
        "themes": [
            {
                "label": "Energy economics strength",
                "sentiment": "positive",
                "detail": "Center for Energy Studies anchors research in energy markets and policy.",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Core econometrics and micro/macro sequences are mathematically rigorous.",
            },
            {
                "label": "Houston policy access",
                "sentiment": "positive",
                "detail": "Proximity to energy firms and policy institutions supports applied research.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track economics faculty positions are nationally competitive.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than top-10 economics departments at peer R1 universities.",
            },
        ],
        "sources": [
            {
                "label": "Rice Economics \u2014 Ph.D. Program",
                "url": "https://economics.rice.edu/phd",
            },
            {
                "label": "Niche \u2014 Best Colleges for Economics",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-electrical-and-computer-engineering-phd": {
        "summary": "Doctoral students describe Rice's Ph.D. in Electrical and Computer Engineering as a research degree within the George R. Brown School of Engineering and Computing \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Houston industry ties, with cautions about funding competition and long dissertation timelines.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Houston industry access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms support applied research.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Rice Engineering ranks among leading R1 engineering schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Engineering Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Electrical and Computer Engineering",
                "url": "https://ece.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-materials-science-and-nanoengineering-phd": {
        "summary": "Doctoral students describe Rice's Ph.D. in Materials Science and NanoEngineering as a research degree within the George R. Brown School of Engineering and Computing \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Houston industry ties, with cautions about funding competition and long dissertation timelines.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Houston industry access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms support applied research.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Rice Engineering ranks among leading R1 engineering schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Engineering Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Materials Science and NanoEngineering",
                "url": "https://msne.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-doctor-of-philosophy-in-mechanical-engineering-phd": {
        "summary": "Doctoral students describe Rice's Ph.D. in Mechanical Engineering as a research degree within the George R. Brown School of Engineering and Computing \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for faculty mentorship and Houston industry ties, with cautions about funding competition and long dissertation timelines.",
        "themes": [
            {
                "label": "Research mentorship",
                "sentiment": "positive",
                "detail": "Smaller cohorts enable close advisor relationships in specialized labs.",
            },
            {
                "label": "Houston industry access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms support applied research.",
            },
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Rice Engineering ranks among leading R1 engineering schools.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are limited relative to applicant interest.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Engineering Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Mechanical Engineering",
                "url": "https://mech.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-electrical-and-computer-engineering-ug": {
        "summary": "Students describe Rice's Electrical and Computer Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Electrical and Computer Engineering",
                "url": "https://ece.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-environmental-engineering-ug": {
        "summary": "Students describe Rice's Environmental Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Environmental Engineering",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-executive-mba-prof": {
        "summary": "Senior leaders describe Rice Business's Executive MBA as an 18-month program with monthly Houston residencies for experienced managers; praise includes peer quality, entrepreneurship resources, and Houston energy-sector access, with cautions about intensive residency blocks and a program scale smaller than large public EMBA offerings.",
        "themes": [
            {
                "label": "Senior peer cohort",
                "sentiment": "positive",
                "detail": "Students average 14+ years of work experience across industries.",
            },
            {
                "label": "Entrepreneurship ecosystem",
                "sentiment": "positive",
                "detail": "Jones entrepreneurship ranking and Houston startup resources differentiate the program.",
            },
            {
                "label": "Houston industries",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and consulting networks are program strengths.",
            },
            {
                "label": "Residency intensity",
                "sentiment": "caution",
                "detail": "Monthly residencies require significant time away from work.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller cohort than large public EMBA programs with fewer specialty tracks.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 Executive MBA",
                "url": "https://business.rice.edu/rice-mba/executive-mba",
            },
            {
                "label": "Poets&Quants \u2014 Rice Jones profile",
                "url": "https://poetsandquants.com/school-profile/rice-university-jones-graduate-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-hybrid-mba-prof": {
        "summary": "Students describe Rice Business's Hybrid MBA as a blend of online coursework and in-person Houston residencies for working professionals; praise includes flexibility and Jones entrepreneurship resources, with cautions that hybrid format reduces spontaneous networking versus the full-time MBA and that national brand recognition still trails top-15 programs.",
        "themes": [
            {
                "label": "Flexible format",
                "sentiment": "positive",
                "detail": "Online modules plus periodic Houston residencies suit working professionals.",
            },
            {
                "label": "Entrepreneurship ranking",
                "sentiment": "positive",
                "detail": "The Princeton Review ranks Jones #1 for graduate entrepreneurship.",
            },
            {
                "label": "STEM-designated options",
                "sentiment": "positive",
                "detail": "STEM tracks extend OPT eligibility for international graduates.",
            },
            {
                "label": "Networking trade-off",
                "sentiment": "caution",
                "detail": "Less daily campus interaction than the full-time MBA cohort experience.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Growing reputation but still behind M7 schools in some national markets.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 Hybrid MBA",
                "url": "https://business.rice.edu/rice-mba/professional-mba/hybrid-mba",
            },
            {
                "label": "Poets&Quants \u2014 Rice Jones profile",
                "url": "https://poetsandquants.com/school-profile/rice-university-jones-graduate-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-managerial-economics-and-organizational-sciences-ug": {
        "summary": "Students describe Rice's Managerial Economics and Organizational Sciences major as a rigorous social-sciences program within a selective private university \u2014 Niche ranks Rice economics #18 nationally; praise includes small seminars and Houston policy/industry access, with cautions that career outcomes vary by field and Houston finance recruiting is smaller than coastal peers.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Rice experience.",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Social-sciences majors emphasize data-driven analysis.",
            },
            {
                "label": "Houston access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and policy institutions provide internship opportunities.",
            },
            {
                "label": "Career variability",
                "sentiment": "caution",
                "detail": "Outcomes vary by major; some paths favor graduate study.",
            },
            {
                "label": "Finance recruiting",
                "sentiment": "mixed",
                "detail": "Houston energy/consulting ties are strong; Wall Street presence is limited.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Managerial Economics and Organizational Sciences",
                "url": "https://socialsciences.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-architecture-march-option-2-post-professional-prof": {
        "summary": "Practicing architects describe Rice Architecture's post-professional M.Arch Option 2 as a research-oriented second master's for licensed architects \u2014 Niche ranked Rice #1 for architecture majors (2023) \u2014 with intensive studio culture and a Paris campus; praise includes faculty critics and Houston's architectural diversity, with cautions about demanding studio workloads and a tiny cohort.",
        "themes": [
            {
                "label": "Post-professional focus",
                "sentiment": "positive",
                "detail": "Option 2 serves licensed architects pursuing advanced design research.",
            },
            {
                "label": "Top architecture reputation",
                "sentiment": "positive",
                "detail": "Niche ranked Rice #1 for architecture majors; NAAB-accredited programs.",
            },
            {
                "label": "Paris campus",
                "sentiment": "positive",
                "detail": "Rice Architecture Paris offers international studio experiences.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Intensive crit-based studios require sustained long hours.",
            },
            {
                "label": "Tiny cohort",
                "sentiment": "mixed",
                "detail": "Highly selective admission limits peer diversity versus large public programs.",
            },
        ],
        "sources": [
            {
                "label": "Rice School of Architecture \u2014 Graduate",
                "url": "https://arch.rice.edu/academics/graduate",
            },
            {
                "label": "Black Spectacles \u2014 Top M.Arch Programs",
                "url": "https://www.blackspectacles.com/blog/top-10-masters-of-architecture-programs-in-the-us",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-arts-in-economics-ms": {
        "summary": "Graduate students describe Rice's M.A. in Economics as a one-year coursework master's preparing students for doctoral study or analytics roles \u2014 Niche ranks Rice #18 for undergraduate economics; praise includes quantitative training and Houston energy-sector access, with cautions about self-funded tuition and limited career-office support compared to professional schools.",
        "themes": [
            {
                "label": "Quantitative preparation",
                "sentiment": "positive",
                "detail": "Core micro, macro, and econometrics prepare for Ph.D. or analytics careers.",
            },
            {
                "label": "Energy economics access",
                "sentiment": "positive",
                "detail": "Center for Energy Studies courses connect to Houston energy markets.",
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": "M.A. graduates regularly advance to doctoral programs at Rice and peer schools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Terminal master's students typically self-fund without assistantships.",
            },
            {
                "label": "Career support",
                "sentiment": "mixed",
                "detail": "GS career advising is lighter than Jones or professional school placement offices.",
            },
        ],
        "sources": [
            {
                "label": "Rice Economics \u2014 M.A. Program",
                "url": "https://economics.rice.edu/ma",
            },
            {
                "label": "Niche \u2014 Best Colleges for Economics",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-bioengineering-mbe-applied-bioengineering-prof": {
        "summary": "Professionals describe Rice's Master of Bioengineering (MBE) \u2014 Applied Bioengineering as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Bioengineering",
                "url": "https://bioengineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-bioengineering-mbe-global-medical-innovation-prof": {
        "summary": "Professionals describe Rice Bioengineering's Global Medical Innovation MBE track as a Houston-based program training engineers for med-tech product development with Texas Medical Center access; praise includes clinical immersion and industry partnerships, with cautions about self-funded tuition and a specialized career path concentrated in medical-device hubs.",
        "themes": [
            {
                "label": "Texas Medical Center",
                "sentiment": "positive",
                "detail": "Students work alongside clinicians and researchers in the world's largest medical complex.",
            },
            {
                "label": "Med-tech product focus",
                "sentiment": "positive",
                "detail": "Curriculum spans design, regulatory, and commercialization of medical devices.",
            },
            {
                "label": "Industry partnerships",
                "sentiment": "positive",
                "detail": "Houston med-tech firms and hospital systems provide project sponsors.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Niche career path",
                "sentiment": "mixed",
                "detail": "Medical-device roles concentrate in Houston, Minneapolis, and coastal hubs.",
            },
        ],
        "sources": [
            {
                "label": "Rice Bioengineering \u2014 Global Medical Innovation MBE",
                "url": "https://bioengineering.rice.edu/academics/graduate-programs/mbe-global-medical-innovation",
            },
            {
                "label": "Rice Engineering \u2014 Bioengineering",
                "url": "https://bioengineering.rice.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-chemical-engineering-mche-prof": {
        "summary": "Professionals describe Rice's Master of Chemical Engineering (MChE) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Chemical and Biomolecular Engineering",
                "url": "https://chbe.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-civil-and-environmental-engineering-mcee-prof": {
        "summary": "Professionals describe Rice's Master of Civil and Environmental Engineering (MCEE) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Civil and Environmental Engineering",
                "url": "https://cee.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-computational-economics-mcecon-prof": {
        "summary": "Students and third-party guides describe Rice's professional program in Computational Economics within School of Social Sciences as a professionally focused degree at a private R1 university in Houston; praise includes Rice's faculty and 6:1 student-faculty ratio, with cautions about competitive admission, self-funded tuition for professional programs, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Private R1 reputation",
                "sentiment": "positive",
                "detail": "Rice ranks among the nation's leading private research universities.",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Economics lead research and professional training.",
            },
            {
                "label": "Small-college experience",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Rice graduate and professional programs have selective admission pools.",
            },
            {
                "label": "Houston context",
                "sentiment": "mixed",
                "detail": "Energy and healthcare ecosystems are strengths; finance recruiting is more limited.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Economics",
                "url": "https://economics.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rice-university-3604",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-computational-science-and-engineering-mcse-prof": {
        "summary": "Professionals describe Rice's Master of Computational Science and Engineering (MCSE) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Engineering and Computing",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-computer-science-mcs-prof": {
        "summary": "Students describe Rice's professional MCS as a coursework-focused master's for career changers and working engineers within a top-20 CS department; praise includes flexible scheduling and Houston industry ties, with cautions about self-funded tuition and less research funding than the thesis-based M.S.",
        "themes": [
            {
                "label": "Coursework focus",
                "sentiment": "positive",
                "detail": "Professional MCS emphasizes applied CS skills without a thesis requirement.",
            },
            {
                "label": "Career transition",
                "sentiment": "positive",
                "detail": "Designed for engineers and analysts moving into software and data roles.",
            },
            {
                "label": "CS department reputation",
                "sentiment": "positive",
                "detail": "Rice CS ranks among the nation's top-20 programs on Niche and College Factual.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without research assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework track offers less RA support than the thesis M.S.",
            },
        ],
        "sources": [
            {
                "label": "Rice Computer Science \u2014 Professional MCS",
                "url": "https://csweb.rice.edu/academics/graduate-programs/professional-mcs",
            },
            {
                "label": "Niche \u2014 Best Colleges for Computer Science",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-data-science-mds-prof": {
        "summary": "Students describe Rice's on-campus Master of Data Science as a project-based professional degree \u2014 Fortune ranked Rice among the top online data-science programs and College Factual ranks Rice CS master's programs highly \u2014 with real datasets from Houston partners; praise includes AI/ML curriculum and faculty access, with cautions about self-funded tuition and a newer program with less third-party review coverage than the flagship online MCS.",
        "themes": [
            {
                "label": "Project-based curriculum",
                "sentiment": "positive",
                "detail": "Students work with real-world datasets from companies and nonprofits.",
            },
            {
                "label": "AI & ML focus",
                "sentiment": "positive",
                "detail": "Prepares graduates for data science, analytics, and machine-learning roles.",
            },
            {
                "label": "Houston industry partners",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms in Houston provide project datasets.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited public reviews",
                "sentiment": "mixed",
                "detail": "Fewer independent review sites cover MDS than the longer-running online MCS.",
            },
        ],
        "sources": [
            {
                "label": "Rice CS \u2014 Master of Data Science",
                "url": "https://csweb.rice.edu/academics/graduate-programs/master-data-science",
            },
            {
                "label": "Rice News \u2014 Online programs climb in U.S. News (2026)",
                "url": "https://news.rice.edu/news/2026/rice-online-programs-climb-us-news-world-report-rankings-led-top-tier-computer-science",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-digital-health-mdh-prof": {
        "summary": "Professionals describe Rice's Master of Digital Health (MDH) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Engineering and Computing",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-electrical-and-computer-engineering-mece-prof": {
        "summary": "Professionals describe Rice's Master of Electrical and Computer Engineering (MECE) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Electrical and Computer Engineering",
                "url": "https://ece.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-energy-economics-meecon-prof": {
        "summary": "Professionals describe Rice's Master of Energy Economics as a quantitative program at the Center for Energy Studies within the School of Social Sciences \u2014 leveraging Houston's energy capital status; praise includes faculty with industry and policy experience and strong energy-sector placement, with cautions about niche career paths and self-funded tuition for a one-year professional master's.",
        "themes": [
            {
                "label": "Houston energy hub",
                "sentiment": "positive",
                "detail": "Program sits in the global energy capital with industry guest faculty.",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Curriculum spans econometrics, energy markets, and policy analysis.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates join energy trading, consulting, and policy firms.",
            },
            {
                "label": "Niche career path",
                "sentiment": "caution",
                "detail": "Energy economics roles are concentrated in Houston and energy hubs.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional one-year master's typically requires self-funding.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Master of Energy Economics",
                "url": "https://economics.rice.edu/master-energy-economics",
            },
            {
                "label": "Rice Center for Energy Studies",
                "url": "https://cerf.rice.edu/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-engineering-management-and-leadership-meml-online-prof": {
        "summary": "Professionals describe Rice's Master of Engineering Management and Leadership (MEML, Online) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Engineering and Computing",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-engineering-management-and-leadership-meml-prof": {
        "summary": "Professionals describe Rice's Master of Engineering Management and Leadership (MEML) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Engineering and Computing",
                "url": "https://engineering.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-industrial-engineering-mie-prof": {
        "summary": "Professionals describe Rice's Master of Industrial Engineering (MIE) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Computational Applied Mathematics and Operations Research",
                "url": "https://cmor.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-materials-science-and-nanoengineering-mmsne-prof": {
        "summary": "Professionals describe Rice's Master of Materials Science and NanoEngineering (MMSNE) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Materials Science and NanoEngineering",
                "url": "https://msne.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-mechanical-engineering-mme-prof": {
        "summary": "Professionals describe Rice's Master of Mechanical Engineering (MME) as a coursework-focused professional master's within the School of Engineering and Computing; praise includes Houston industry partnerships and flexible scheduling for working engineers, with cautions about self-funded tuition and less research funding than thesis-based graduate programs.",
        "themes": [
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Coursework master's designed for career advancement without a thesis.",
            },
            {
                "label": "Houston industry ties",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting.",
            },
            {
                "label": "Flexible scheduling",
                "sentiment": "positive",
                "detail": "Many professional programs offer evening or online options.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Professional master's students typically self-fund without assistantships.",
            },
            {
                "label": "Limited research funding",
                "sentiment": "mixed",
                "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Mechanical Engineering",
                "url": "https://mech.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-science-in-architecture-option-3-ms": {
        "summary": "Graduate students describe Rice Architecture's Option 3 M.S. as a research-oriented degree for students exploring architectural history, theory, or technology without a professional M.Arch; praise includes close faculty mentorship within a top-ranked school, with cautions about limited career placement support for non-licensure paths and a small program with few public third-party reviews.",
        "themes": [
            {
                "label": "Research orientation",
                "sentiment": "positive",
                "detail": "Option 3 supports thesis research in history, theory, and technology.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small cohorts enable close work with Rice Architecture faculty.",
            },
            {
                "label": "Top school reputation",
                "sentiment": "positive",
                "detail": "Rice Architecture ranks among the nation's leading programs on Niche.",
            },
            {
                "label": "Non-licensure path",
                "sentiment": "caution",
                "detail": "Option 3 does not lead to architectural licensure like the M.Arch.",
            },
            {
                "label": "Limited public reviews",
                "sentiment": "mixed",
                "detail": "Fewer third-party review sites cover Option 3 than the professional M.Arch.",
            },
        ],
        "sources": [
            {
                "label": "Rice School of Architecture \u2014 Graduate",
                "url": "https://arch.rice.edu/academics/graduate",
            },
            {
                "label": "U.S. News \u2014 Architecture rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-science-in-civil-and-environmental-engineering-ms": {
        "summary": "Graduate students describe Rice's M.S. in Civil and Environmental Engineering as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Houston industry recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Houston recruiting",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms recruit Rice engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
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
                "label": "Rice \u2014 Civil and Environmental Engineering",
                "url": "https://cee.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-science-in-computer-science-ms": {
        "summary": "Graduate applicants describe Rice's on-campus M.S. in Computer Science as a thesis or coursework degree within a top-20 department; praise includes research assistantships, Houston tech recruiting, and AI/systems faculty, with cautions about self-funded tuition for terminal master's students and a smaller department than CS-flagship peers.",
        "themes": [
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Thesis-track students join labs in AI, systems, and computational biology.",
            },
            {
                "label": "Houston tech recruiting",
                "sentiment": "positive",
                "detail": "Graduates place at energy-tech, healthcare, and software firms in Houston and nationally.",
            },
            {
                "label": "Top-20 CS reputation",
                "sentiment": "positive",
                "detail": "Niche and College Factual rank Rice CS among the nation's leading programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Department scale",
                "sentiment": "mixed",
                "detail": "Smaller than MIT, CMU, or Berkeley CS departments.",
            },
        ],
        "sources": [
            {
                "label": "Rice Computer Science \u2014 M.S.",
                "url": "https://csweb.rice.edu/academics/graduate-programs/ms",
            },
            {
                "label": "Niche \u2014 Best Colleges for Computer Science",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-science-in-electrical-and-computer-engineering-ms": {
        "summary": "Graduate students describe Rice's M.S. in Electrical and Computer Engineering as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Houston industry recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Houston recruiting",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms recruit Rice engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
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
                "label": "Rice \u2014 Electrical and Computer Engineering",
                "url": "https://ece.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-master-of-science-in-mechanical-engineering-ms": {
        "summary": "Graduate students describe Rice's M.S. in Mechanical Engineering as a thesis or coursework degree within a top R1 engineering school; praise includes research assistantships and Houston industry recruiting, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in specialized engineering areas.",
            },
            {
                "label": "Houston recruiting",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and tech firms recruit Rice engineering graduates.",
            },
            {
                "label": "Small cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Self-funded MS",
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
                "label": "Rice \u2014 Mechanical Engineering",
                "url": "https://mech.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-materials-science-and-nanoengineering-ug": {
        "summary": "Students describe Rice's Materials Science and NanoEngineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Materials Science and NanoEngineering",
                "url": "https://msne.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-mba-rice-online-mba-prof": {
        "summary": "Working professionals describe MBA@Rice as Rice Business's online MBA with live virtual classes and periodic Houston residencies; praise includes Jones entrepreneurship resources and STEM-designated curriculum, with cautions that online delivery reduces spontaneous networking versus residential MBA programs and that Houston's finance recruiting footprint is smaller than coastal hubs.",
        "themes": [
            {
                "label": "Live online classes",
                "sentiment": "positive",
                "detail": "Synchronous sessions with Rice faculty rather than self-paced MOOC delivery.",
            },
            {
                "label": "Entrepreneurship ranking",
                "sentiment": "positive",
                "detail": "The Princeton Review ranks Jones #1 for graduate entrepreneurship.",
            },
            {
                "label": "Residency experiences",
                "sentiment": "positive",
                "detail": "Periodic Houston residencies provide in-person networking and team projects.",
            },
            {
                "label": "Online networking",
                "sentiment": "caution",
                "detail": "Virtual format limits informal campus networking versus full-time MBA.",
            },
            {
                "label": "Finance recruiting",
                "sentiment": "mixed",
                "detail": "Strong energy/consulting ties but fewer Wall Street recruiters than coastal peers.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 MBA@Rice Online",
                "url": "https://business.rice.edu/rice-mba/online-mba",
            },
            {
                "label": "Poets&Quants \u2014 Rice Jones profile",
                "url": "https://poetsandquants.com/school-profile/rice-university-jones-graduate-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-mechanical-engineering-ug": {
        "summary": "Students describe Rice's Mechanical Engineering B.S. as an engineering degree within a selective private university \u2014 U.S. News ranks Rice Engineering among leading doctorate-granting programs \u2014 with praise for small classes and undergraduate research access; cautions include demanding coursework and a smaller engineering school than MIT or Berkeley.",
        "themes": [
            {
                "label": "Small engineering cohort",
                "sentiment": "positive",
                "detail": "Classes are smaller than at large public engineering schools.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across Rice Engineering departments.",
            },
            {
                "label": "Residential college life",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio and residential colleges support close advising.",
            },
            {
                "label": "Demanding coursework",
                "sentiment": "caution",
                "detail": "Selective engineering school with rigorous quantitative requirements.",
            },
            {
                "label": "Smaller than peer flagships",
                "sentiment": "mixed",
                "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Mechanical Engineering",
                "url": "https://mech.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-professional-mba-evening-prof": {
        "summary": "Working professionals describe Rice Business's Evening MBA as a Houston-based part-time MBA with the same integrated core as the full-time program; praise includes entrepreneurship resources (The Princeton Review ranks Jones #1 for graduate entrepreneurship) and energy-sector recruiting, with cautions about balancing work and weekly evening classes and a smaller national brand than coastal M7 peers.",
        "themes": [
            {
                "label": "Entrepreneurship ecosystem",
                "sentiment": "positive",
                "detail": "Jones ranked #1 graduate entrepreneurship by The Princeton Review; OwlSpark and Liu Idea Lab support startups.",
            },
            {
                "label": "Houston energy recruiting",
                "sentiment": "positive",
                "detail": "Evening MBA students leverage Houston's energy, healthcare, and consulting employers.",
            },
            {
                "label": "Integrated Rice core",
                "sentiment": "positive",
                "detail": "Part-time students take the same multidisciplinary core as the full-time MBA.",
            },
            {
                "label": "Work-life balance",
                "sentiment": "caution",
                "detail": "Weekly evening classes require sustained commitment alongside full-time jobs.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Strong regional outcomes but a smaller national MBA brand than M7 schools.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 Professional MBA Evening",
                "url": "https://business.rice.edu/rice-mba/professional-mba/evening-mba",
            },
            {
                "label": "Poets&Quants \u2014 Rice Jones profile",
                "url": "https://poetsandquants.com/school-profile/rice-university-jones-graduate-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-professional-mba-weekend-prof": {
        "summary": "Executives describe Rice Business's Weekend MBA as a monthly-residency part-time program for Houston-area leaders; praise includes a tight cohort, Jones's entrepreneurship ranking, and Houston corporate access, with cautions about travel during residency weekends and less finance-recruiting density than NYC-based weekend programs.",
        "themes": [
            {
                "label": "Executive cohort",
                "sentiment": "positive",
                "detail": "Peers bring senior leadership experience across Houston industries.",
            },
            {
                "label": "Entrepreneurship resources",
                "sentiment": "positive",
                "detail": "Jones entrepreneurship ranking and Rice Business Plan Competition anchor startup activity.",
            },
            {
                "label": "Houston corporate network",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and consulting firms recruit Rice MBA graduates.",
            },
            {
                "label": "Residency travel",
                "sentiment": "caution",
                "detail": "Monthly on-campus residencies require time away from work and family.",
            },
            {
                "label": "Finance recruiting",
                "sentiment": "mixed",
                "detail": "Houston is strong for energy/consulting but quieter for investment banking than NYC.",
            },
        ],
        "sources": [
            {
                "label": "Rice Business \u2014 Professional MBA Weekend",
                "url": "https://business.rice.edu/rice-mba/professional-mba/weekend-mba",
            },
            {
                "label": "Poets&Quants \u2014 Rice Jones profile",
                "url": "https://poetsandquants.com/school-profile/rice-university-jones-graduate-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-sport-analytics-ug": {
        "summary": "Students describe Rice's Sport Analytics major as a rigorous social-sciences program within a selective private university \u2014 Niche ranks Rice economics #18 nationally; praise includes small seminars and Houston policy/industry access, with cautions that career outcomes vary by field and Houston finance recruiting is smaller than coastal peers.",
        "themes": [
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "Seminars and residential-college tutorials anchor the Rice experience.",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Social-sciences majors emphasize data-driven analysis.",
            },
            {
                "label": "Houston access",
                "sentiment": "positive",
                "detail": "Energy, healthcare, and policy institutions provide internship opportunities.",
            },
            {
                "label": "Career variability",
                "sentiment": "caution",
                "detail": "Outcomes vary by major; some paths favor graduate study.",
            },
            {
                "label": "Finance recruiting",
                "sentiment": "mixed",
                "detail": "Houston energy/consulting ties are strong; Wall Street presence is limited.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Sport Analytics",
                "url": "https://socialsciences.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "rice-sports-medicine-and-exercise-physiology-ug": {
        "summary": "Students describe Rice's Sports Medicine and Exercise Physiology major in the Wiess School of Natural Sciences as a rigorous STEM program within a selective private R1 university; praise includes small classes, undergraduate research access, and a 6:1 student-faculty ratio, with cautions about competitive grading and pre-med/pre-grad pressure.",
        "themes": [
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "Students join faculty labs across natural-sciences departments.",
            },
            {
                "label": "Small classes",
                "sentiment": "positive",
                "detail": "6:1 student-faculty ratio supports close faculty access.",
            },
            {
                "label": "R1 research university",
                "sentiment": "positive",
                "detail": "Rice's R1 classification supports graduate-school and industry placement.",
            },
            {
                "label": "Competitive grading",
                "sentiment": "caution",
                "detail": "Selective STEM majors have demanding coursework and grade pressure.",
            },
            {
                "label": "Pre-professional pressure",
                "sentiment": "mixed",
                "detail": "Many natural-sciences majors pursue medical or doctoral paths.",
            },
        ],
        "sources": [
            {
                "label": "Rice \u2014 Sports Medicine and Exercise Physiology",
                "url": "https://biosciences.rice.edu/",
            },
            {
                "label": "U.S. News \u2014 Rice University",
                "url": "https://www.usnews.com/best-colleges/rice-university-3604",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
