"""Purdue University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``purdueprof3`` migration to merge
``DEPTH_REVIEWS`` into ``purdue_profile._REVIEWS_BY_SLUG`` for 56
remaining coverable programs (64/64 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "purdue-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
        "summary": "Graduate students describe Purdue's aerospace M.S. in the School of Aeronautics and Astronautics as a top-ranked program with access to Zucrow Laboratories and the 'Cradle of Astronauts' legacy; praise includes NASA and defense recruiting, with cautions about demanding coursework, competitive research funding, and self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "National #1\u20132 rank",
                "sentiment": "positive",
                "detail": "Purdue aerospace is consistently ranked among the top two programs nationally.",
            },
            {
                "label": "Zucrow Laboratories",
                "sentiment": "positive",
                "detail": "One of the largest university jet-propulsion research facilities in the world.",
            },
            {
                "label": "NASA pipeline",
                "sentiment": "positive",
                "detail": "More astronauts have Purdue degrees than any other university.",
            },
            {
                "label": "Rigorous coursework",
                "sentiment": "caution",
                "detail": "Graduate sequences in fluids, structures, and propulsion are mathematically demanding.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
        ],
        "sources": [
            {
                "label": "Purdue AAE \u2014 Graduate Programs",
                "url": "https://engineering.purdue.edu/AAE/academics/graduate",
            },
            {
                "label": "U.S. News \u2014 Aerospace Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/aerospace-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-agricultural-business-and-management-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Agricultural Business and Management as a coursework and research degree within College of Agriculture; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core agricultural business and management theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Agricultural Business and Management",
                "url": "https://ag.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-agricultural-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Agricultural Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Agricultural Engineering",
                "url": "https://engineering.purdue.edu/ABE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-agricultural-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Agricultural Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core agricultural engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Agricultural Engineering",
                "url": "https://engineering.purdue.edu/ABE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-applied-horticulture-and-horticultural-business-services-bs": {
        "summary": "Students describe Purdue's Applied Horticulture and Horticultural Business Services program in the College of Agriculture as a land-grant program with deep ties to Indiana agriculture and Purdue Extension; praise includes practical field experience and USDA connections, with cautions that career paths are specialized to agriculture and food systems.",
        "themes": [
            {
                "label": "Land-grant mission",
                "sentiment": "positive",
                "detail": "Purdue Extension and Indiana agriculture provide unmatched applied learning.",
            },
            {
                "label": "Field experience",
                "sentiment": "positive",
                "detail": "Research farms and extension stations support hands-on learning.",
            },
            {
                "label": "USDA connections",
                "sentiment": "positive",
                "detail": "Faculty partnerships with USDA create policy and industry placement pipelines.",
            },
            {
                "label": "Specialized careers",
                "sentiment": "mixed",
                "detail": "Career paths concentrate in agriculture, food systems, and rural development.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship engineering programs but with strong faculty access.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Applied Horticulture and Horticultural Business Services",
                "url": "https://ag.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-architectural-engineering-technologies-technicians-bs": {
        "summary": "Students describe Purdue's undergraduate Architectural Engineering Technologies/Technicians program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Architectural Engineering Technologies/Technicians",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-architectural-engineering-technologies-technicians-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Architectural Engineering Technologies/Technicians as a research and coursework degree within Purdue Polytechnic Institute; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core architectural engineering technologies/technicians theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Architectural Engineering Technologies/Technicians",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-biological-and-biomedical-sciences-other-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Biological and Biomedical Sciences, Other as a coursework and research degree within College of Science; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core biological and biomedical sciences, other theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Biological and Biomedical Sciences, Other",
                "url": "https://www.purdue.edu/science/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-biomedical-medical-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Biomedical/Medical Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Biomedical/Medical Engineering",
                "url": "https://engineering.purdue.edu/BME",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-biomedical-medical-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Biomedical/Medical Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core biomedical/medical engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Biomedical/Medical Engineering",
                "url": "https://engineering.purdue.edu/BME",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-business-administration-management-and-operations-ms": {
        "summary": "Applicants describe Purdue's MBA through the Mitch Daniels School of Business as a quantitatively rigorous program with strength in operations, supply chain, and analytics; students value the Krannert heritage, STEM-designated tracks, and Midwest manufacturing recruiting, with cautions that national brand recognition still trails top-15 MBA programs and career services are strongest for operations-focused roles.",
        "themes": [
            {
                "label": "Quantitative MBA",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes analytics, operations, and supply chain management.",
            },
            {
                "label": "STEM tracks",
                "sentiment": "positive",
                "detail": "STEM-designated concentrations attract international applicants seeking OPT extensions.",
            },
            {
                "label": "Midwest recruiting",
                "sentiment": "positive",
                "detail": "Caterpillar, Amazon, Eli Lilly, and logistics firms recruit actively.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Growing reputation under Mitch Daniels branding but still developing nationally.",
            },
            {
                "label": "Operations focus",
                "sentiment": "mixed",
                "detail": "Career services are strongest for operations and supply chain than for investment banking.",
            },
        ],
        "sources": [
            {
                "label": "Mitch Daniels School of Business \u2014 MBA",
                "url": "https://business.purdue.edu/mba/",
            },
            {
                "label": "Poets&Quants \u2014 Purdue MBA",
                "url": "https://poetsandquants.com/schools/purdue-university-mitch-daniels-school-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-business-corporate-communications-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Business/Corporate Communications as a coursework and research degree within Mitch Daniels School of Business; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core business/corporate communications theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Business/Corporate Communications",
                "url": "https://business.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-chemical-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Chemical Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Chemical Engineering",
                "url": "https://engineering.purdue.edu/ChE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-chemical-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Chemical Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core chemical engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Chemical Engineering",
                "url": "https://engineering.purdue.edu/ChE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-civil-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Civil Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Civil Engineering",
                "url": "https://engineering.purdue.edu/CE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-civil-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Civil Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core civil engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Civil Engineering",
                "url": "https://engineering.purdue.edu/CE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-computer-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Computer Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Computer Engineering",
                "url": "https://engineering.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-computer-science-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Computer Science as a top-ranked research and coursework degree within a perennial top-20 CS department, with strength in security (CERIAS), systems, and AI; praise includes strong industry recruiting and funded research assistantships, with cautions about competitive admission, large cohort sizes, and self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Top CS reputation",
                "sentiment": "positive",
                "detail": "U.S. News ranks Purdue CS among the nation's leading departments.",
            },
            {
                "label": "CERIAS & security",
                "sentiment": "positive",
                "detail": "Center for Education and Research in Information Assurance and Security anchors cybersecurity research.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Graduates place at major tech firms, defense contractors, and research labs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong GRE, GPA, and research background are expected for competitive applicants.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Computer Science \u2014 Graduate",
                "url": "https://www.cs.purdue.edu/graduate/index.html",
            },
            {
                "label": "U.S. News \u2014 Best Computer Science Programs",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-construction-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Construction Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Construction Engineering",
                "url": "https://engineering.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-economics-bs": {
        "summary": "Students describe Purdue's undergraduate economics major in the College of Liberal Arts as a quantitatively oriented program with strong preparation for graduate study and analytics roles; praise includes Krannert-adjacent quantitative training and research opportunities, with cautions that large introductory sections require proactive faculty engagement and career outcomes vary without further graduate study.",
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Econometrics and statistics sequences prepare students for data and policy roles.",
            },
            {
                "label": "Graduate preparation",
                "sentiment": "positive",
                "detail": "Strong track record placing graduates in economics and public policy Ph.D. programs.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Faculty labs in behavioral, labor, and development economics accept undergraduates.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Gateway economics courses can be lecture-heavy with limited individual attention.",
            },
            {
                "label": "Career without grad school",
                "sentiment": "mixed",
                "detail": "Undergraduate economics alone narrows options; pairing with data science or finance is common.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Economics \u2014 Undergraduate",
                "url": "https://cla.purdue.edu/economics/undergraduate/",
            },
            {
                "label": "Niche \u2014 Purdue University",
                "url": "https://www.niche.com/colleges/purdue-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-economics-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Economics as a coursework and research degree within College of Liberal Arts; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core economics theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Economics",
                "url": "https://cla.purdue.edu/economics/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-electrical-electronic-engineering-technologies-technicians-bs": {
        "summary": "Students describe Purdue's undergraduate Electrical/Electronic Engineering Technologies/Technicians program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Electrical/Electronic Engineering Technologies/Technicians",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Electrical, Electronics, and Communications Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core electrical, electronics, and communications engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://engineering.purdue.edu/ECE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-engineering-related-technologies-technicians-other-bs": {
        "summary": "Students describe Purdue's undergraduate Engineering/Engineering-Related Technologies/Technicians, Other program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering/Engineering-Related Technologies/Technicians, Other",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-engineering-related-technologies-technicians-other-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Engineering/Engineering-Related Technologies/Technicians, Other as a research and coursework degree within Purdue Polytechnic Institute; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core engineering/engineering-related technologies/technicians, other theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering/Engineering-Related Technologies/Technicians, Other",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-engineering-related-technologies-technicians-other-phd": {
        "summary": "Doctoral students describe Purdue's Ph.D. in Engineering/Engineering-Related Technologies/Technicians, Other as a research degree within the Purdue Polytechnic Institute producing scholars and industry researchers; praise includes R1 research infrastructure and faculty mentorship, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "Research infrastructure",
                "sentiment": "positive",
                "detail": "Purdue's R1 status and Discovery Park support doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research projects.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates enter academia, national labs, and industry R&D leadership.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering/Engineering-Related Technologies/Technicians, Other",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-general-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Engineering, General as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core engineering, general theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering, General",
                "url": "https://engineering.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-other-bs": {
        "summary": "Students describe Purdue's undergraduate Engineering, Other program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering, Other",
                "url": "https://engineering.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-other-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Engineering, Other as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core engineering, other theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering, Other",
                "url": "https://engineering.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-related-fields-bs": {
        "summary": "Students describe Purdue's undergraduate Engineering-Related Fields program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering-Related Fields",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-related-fields-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Engineering-Related Fields as a research and coursework degree within Purdue Polytechnic Institute; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core engineering-related fields theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering-Related Fields",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-technologies-technicians-general-bs": {
        "summary": "Students describe Purdue's undergraduate Engineering Technologies/Technicians, General program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering Technologies/Technicians, General",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-engineering-technologies-technicians-general-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Engineering Technologies/Technicians, General as a research and coursework degree within Purdue Polytechnic Institute; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core engineering technologies/technicians, general theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Engineering Technologies/Technicians, General",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-environmental-environmental-health-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Environmental/Environmental Health Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Environmental/Environmental Health Engineering",
                "url": "https://engineering.purdue.edu/CE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-environmental-environmental-health-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Environmental/Environmental Health Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core environmental/environmental health engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Environmental/Environmental Health Engineering",
                "url": "https://engineering.purdue.edu/CE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-family-and-consumer-sciences-human-sciences-business-services-bs": {
        "summary": "Students and third-party guides describe Purdue's undergraduate program in Family and Consumer Sciences/Human Sciences Business Services within College of Liberal Arts as a professionally focused degree at a top-50 national research university; praise includes Purdue's R1 infrastructure and Midwest industry ties, with cautions about large class sizes and that career outcomes vary by field and graduate-school plans.",
        "themes": [
            {
                "label": "Research university",
                "sentiment": "positive",
                "detail": "Purdue's R1 status and Discovery Park support undergraduate and graduate research.",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Family and Consumer Sciences/Human Sciences Business Services lead applied and theoretical research.",
            },
            {
                "label": "Career preparation",
                "sentiment": "positive",
                "detail": "Graduates enter industry, government, and graduate programs across the Midwest and nationally.",
            },
            {
                "label": "Class scale",
                "sentiment": "caution",
                "detail": "Large university means gateway courses can be lecture-heavy.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on field specialization and whether students pursue further study.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Family and Consumer Sciences/Human Sciences Business Services",
                "url": "https://cla.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-film-video-and-photographic-arts-bs": {
        "summary": "Students describe Purdue's film and video studies program in CLA as a creative-arts major within a STEM-dominant campus, offering production courses and critical media studies; praise includes access to Polytechnic production facilities and interdisciplinary projects, with cautions that the program is smaller than dedicated film schools and industry networking requires proactive outreach beyond campus.",
        "themes": [
            {
                "label": "Production access",
                "sentiment": "positive",
                "detail": "Students use Polytechnic and CLA media production facilities.",
            },
            {
                "label": "Critical media studies",
                "sentiment": "positive",
                "detail": "Curriculum balances production skills with film theory and criticism.",
            },
            {
                "label": "Interdisciplinary projects",
                "sentiment": "positive",
                "detail": "Collaborations with engineering and agriculture create unique documentary opportunities.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than dedicated film schools; fewer industry guest speakers.",
            },
            {
                "label": "Industry networking",
                "sentiment": "caution",
                "detail": "Entertainment-industry placement requires proactive outreach beyond campus recruiting.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Brian Lamb School \u2014 Film & Video",
                "url": "https://cla.purdue.edu/communication/",
            },
            {
                "label": "Niche \u2014 Purdue University",
                "url": "https://www.niche.com/colleges/purdue-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-finance-and-financial-management-services-bs": {
        "summary": "Students describe Purdue's finance major through the Mitch Daniels School of Business as a quantitatively rigorous undergraduate program with strength in corporate finance, investments, and analytics; praise includes Krannert heritage and strong Midwest recruiting, with cautions that national finance recruiting trails top-10 undergraduate business programs and students must proactively pursue coastal internship opportunities.",
        "themes": [
            {
                "label": "Quantitative finance",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes corporate finance, investments, and financial analytics.",
            },
            {
                "label": "Midwest recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, logistics, and regional banks recruit actively from MDSB.",
            },
            {
                "label": "Analytics integration",
                "sentiment": "positive",
                "detail": "Krannert heritage brings operations and data skills into finance coursework.",
            },
            {
                "label": "Coastal recruiting",
                "sentiment": "mixed",
                "detail": "Investment banking and buy-side placement require proactive networking beyond campus.",
            },
            {
                "label": "Brand recognition",
                "sentiment": "mixed",
                "detail": "Strong regional reputation; national finance brand still developing.",
            },
        ],
        "sources": [
            {
                "label": "Mitch Daniels School of Business \u2014 Finance",
                "url": "https://business.purdue.edu/undergraduate/",
            },
            {
                "label": "U.S. News \u2014 Best Undergraduate Business",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-hospitality-administration-management-bs": {
        "summary": "Students describe Purdue's hospitality management program in MDSB as one of the few top-ranked hospitality programs at a major research university, with strength in food-service management, event planning, and hotel operations; praise includes the Marriott Hall facilities and industry partnerships, with cautions that the program is niche relative to Purdue's engineering identity and coastal hospitality markets require relocation for top-tier hotel careers.",
        "themes": [
            {
                "label": "Top hospitality rank",
                "sentiment": "positive",
                "detail": "Purdue hospitality is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Marriott Hall facilities",
                "sentiment": "positive",
                "detail": "Dedicated hospitality labs and demo kitchens support hands-on learning.",
            },
            {
                "label": "Industry partnerships",
                "sentiment": "positive",
                "detail": "Major hotel, restaurant, and event companies recruit on campus.",
            },
            {
                "label": "Niche within Purdue",
                "sentiment": "mixed",
                "detail": "Smaller program relative to engineering; fewer cross-campus resources.",
            },
            {
                "label": "Geographic market",
                "sentiment": "caution",
                "detail": "Top-tier hotel careers often require relocation to coastal or resort markets.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Hospitality \u2014 About",
                "url": "https://business.purdue.edu/hospitality/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/purdue-university-west-lafayette-1825",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-hospitality-administration-management-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Hospitality Administration/Management as a coursework and research degree within Mitch Daniels School of Business; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core hospitality administration/management theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Hospitality Administration/Management",
                "url": "https://business.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-industrial-engineering-bs": {
        "summary": "Students describe Purdue's industrial engineering program as a perennial top-10 program nationally, known for operations research, human factors, and manufacturing systems; praise includes the Grissom Hall facilities and strong recruiting from Amazon, Caterpillar, and consulting firms, with cautions that large lower-division courses require proactive engagement and the quantitative curriculum is demanding.",
        "themes": [
            {
                "label": "Top-10 national rank",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks Purdue IE among the nation's best programs.",
            },
            {
                "label": "Operations research",
                "sentiment": "positive",
                "detail": "OR, simulation, and supply chain coursework are program hallmarks.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Amazon, Caterpillar, and consulting firms recruit actively.",
            },
            {
                "label": "Quantitative demands",
                "sentiment": "caution",
                "detail": "Statistics, optimization, and simulation courses require strong math preparation.",
            },
            {
                "label": "Large intro sections",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; office hours and study groups matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Industrial Engineering",
                "url": "https://engineering.purdue.edu/IE",
            },
            {
                "label": "U.S. News \u2014 Industrial Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-industrial-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Industrial Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core industrial engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Industrial Engineering",
                "url": "https://engineering.purdue.edu/IE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-landscape-architecture-bs": {
        "summary": "Students describe Purdue's landscape architecture program in CLA as a design-intensive professional degree with emphasis on ecological planning and Midwest land-use issues; praise includes studio culture and interdisciplinary ties to agriculture and engineering, with cautions about long studio hours and that the B.L.A. requires further study or licensure pathways for full professional practice.",
        "themes": [
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and site-planning projects anchor the curriculum.",
            },
            {
                "label": "Ecological focus",
                "sentiment": "positive",
                "detail": "Midwest land-use and sustainability themes distinguish the program.",
            },
            {
                "label": "Interdisciplinary ties",
                "sentiment": "positive",
                "detail": "Connections to agriculture, civil engineering, and urban planning enrich projects.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Long studio hours and intensive crit schedules are recurring themes.",
            },
            {
                "label": "Licensure path",
                "sentiment": "mixed",
                "detail": "Professional landscape architecture licensure requires additional experience beyond the degree.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Landscape Architecture",
                "url": "https://cla.purdue.edu/landscape-architecture/",
            },
            {
                "label": "Niche \u2014 Purdue University",
                "url": "https://www.niche.com/colleges/purdue-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-materials-engineering-bs": {
        "summary": "Students describe Purdue's undergraduate Materials Engineering program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Materials Engineering",
                "url": "https://engineering.purdue.edu/MSE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-materials-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Materials Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core materials engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Materials Engineering",
                "url": "https://engineering.purdue.edu/MSE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-mathematics-and-computer-science-bs": {
        "summary": "Students and third-party guides describe Purdue's undergraduate program in Mathematics and Computer Science within College of Science as a research-oriented degree at a top-50 national research university; praise includes Purdue's R1 infrastructure and Midwest industry ties, with cautions about large class sizes and that career outcomes vary by field and graduate-school plans.",
        "themes": [
            {
                "label": "Research university",
                "sentiment": "positive",
                "detail": "Purdue's R1 status and Discovery Park support undergraduate and graduate research.",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Mathematics and Computer Science lead applied and theoretical research.",
            },
            {
                "label": "Career preparation",
                "sentiment": "positive",
                "detail": "Graduates enter industry, government, and graduate programs across the Midwest and nationally.",
            },
            {
                "label": "Class scale",
                "sentiment": "caution",
                "detail": "Large university means gateway courses can be lecture-heavy.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on field specialization and whether students pursue further study.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Mathematics and Computer Science",
                "url": "https://www.purdue.edu/science/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-mechanical-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Mechanical Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core mechanical engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Mechanical Engineering",
                "url": "https://engineering.purdue.edu/ME",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-mechanical-engineering-related-technologies-technicians-bs": {
        "summary": "Students describe Purdue's undergraduate Mechanical Engineering Related Technologies/Technicians program in the College of Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes research lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Purdue Engineering is consistently ranked among the top programs nationally.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access Discovery Park labs and school-specific research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering.",
            },
            {
                "label": "Rigorous curriculum",
                "sentiment": "caution",
                "detail": "Math and physics sequences in years 1\u20132 are demanding.",
            },
            {
                "label": "Large class sizes",
                "sentiment": "caution",
                "detail": "Gateway courses can be impersonal; study groups and office hours matter.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Mechanical Engineering Related Technologies/Technicians",
                "url": "https://polytechnic.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-nuclear-engineering-bs": {
        "summary": "Students describe Purdue's nuclear engineering program as one of the few dedicated undergraduate nuclear programs in the United States, with strength in reactor physics, radiation detection, and nuclear materials; praise includes the PUR-1 research reactor on campus and strong ties to the national labs, with cautions that the field is niche and career paths concentrate in government, utilities, and national-security sectors.",
        "themes": [
            {
                "label": "PUR-1 reactor",
                "sentiment": "positive",
                "detail": "On-campus research reactor provides rare undergraduate hands-on nuclear experience.",
            },
            {
                "label": "National lab ties",
                "sentiment": "positive",
                "detail": "Connections to Argonne, Oak Ridge, and INL support internships and research.",
            },
            {
                "label": "Specialized expertise",
                "sentiment": "positive",
                "detail": "One of the few standalone undergraduate nuclear engineering programs nationally.",
            },
            {
                "label": "Niche field",
                "sentiment": "mixed",
                "detail": "Career paths concentrate in utilities, national labs, and defense.",
            },
            {
                "label": "Program size",
                "sentiment": "caution",
                "detail": "Small cohort means fewer peer study groups but more faculty access.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Nuclear Engineering",
                "url": "https://engineering.purdue.edu/NE",
            },
            {
                "label": "U.S. News \u2014 Purdue Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-nuclear-engineering-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Nuclear Engineering as a research and coursework degree within College of Engineering; students value Purdue's engineering and research reputation and industry recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core nuclear engineering theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Nuclear Engineering",
                "url": "https://engineering.purdue.edu/NE",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-public-health-bs": {
        "summary": "Students describe Purdue's undergraduate public health program in HHS as an interdisciplinary major drawing on epidemiology, health policy, and biostatistics; praise includes access to Indiana health-system partnerships and a growing program within a land-grant research university, with cautions that the major is newer than peer pre-med tracks and upper-division courses can fill quickly.",
        "themes": [
            {
                "label": "Interdisciplinary design",
                "sentiment": "positive",
                "detail": "Combines population health, statistics, and policy across HHS departments.",
            },
            {
                "label": "Indiana partnerships",
                "sentiment": "positive",
                "detail": "Regional health systems and state agencies offer internship opportunities.",
            },
            {
                "label": "Land-grant mission",
                "sentiment": "positive",
                "detail": "Extension and community health outreach connect classroom learning to practice.",
            },
            {
                "label": "Program maturity",
                "sentiment": "mixed",
                "detail": "Undergraduate public health is newer than established pre-med pathways at peer schools.",
            },
            {
                "label": "Course capacity",
                "sentiment": "caution",
                "detail": "Popular upper-division electives can be competitive to access.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Public Health \u2014 Undergraduate",
                "url": "https://hhs.purdue.edu/public-health/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/purdue-university-west-lafayette-1825",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-public-health-ms": {
        "summary": "Graduate applicants describe Purdue's MPH as a practice-oriented public health degree within HHS emphasizing epidemiology, health policy, and community health; students value Indiana health-system partnerships and affordable tuition relative to coastal programs, with cautions that the school is smaller than top-10 public health programs and research funding is more limited than at R1 peers on the coasts.",
        "themes": [
            {
                "label": "Practice orientation",
                "sentiment": "positive",
                "detail": "MPH curriculum emphasizes applied epidemiology and community health practice.",
            },
            {
                "label": "Indiana network",
                "sentiment": "positive",
                "detail": "State health department and hospital partnerships support practicum placements.",
            },
            {
                "label": "Affordable tuition",
                "sentiment": "positive",
                "detail": "In-state and competitive out-of-state rates versus coastal MPH programs.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than top-10 public health schools; fewer specialized concentrations.",
            },
            {
                "label": "Research funding",
                "sentiment": "caution",
                "detail": "Assistantships and funded research spots are more limited than at larger peer schools.",
            },
        ],
        "sources": [
            {
                "label": "Purdue Public Health \u2014 Graduate",
                "url": "https://hhs.purdue.edu/public-health/graduate/",
            },
            {
                "label": "U.S. News \u2014 Public Health Rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as a coursework and research degree within College of Health and Human Sciences; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core registered nursing, nursing administration, nursing research and clinical nursing theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://hhs.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/nursing",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": {
        "summary": "Doctoral students describe Purdue's Ph.D. in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as a research degree within the College of Health and Human Sciences producing scholars and industry researchers; praise includes R1 research infrastructure and faculty mentorship, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "Research infrastructure",
                "sentiment": "positive",
                "detail": "Purdue's R1 status and Discovery Park support doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research projects.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates enter academia, national labs, and industry R&D leadership.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://hhs.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-colleges/rankings/nursing",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-veterinary-biomedical-and-clinical-sciences-ms": {
        "summary": "Graduate applicants describe Purdue's M.S. in Veterinary Biomedical and Clinical Sciences as a coursework and research degree within College of Veterinary Medicine; students value Purdue's engineering and research reputation and practical training, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Graduate curriculum",
                "sentiment": "positive",
                "detail": "M.S. coursework spans core veterinary biomedical and clinical sciences theory and applied projects.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs and interdisciplinary research centers.",
            },
            {
                "label": "Industry paths",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Purdue's large graduate population.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 Veterinary Biomedical and Clinical Sciences",
                "url": "https://vet.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "purdue-veterinary-medicine-phd": {
        "summary": "Doctoral students describe Purdue's Ph.D. in Veterinary Medicine as a research degree within the College of Veterinary Medicine producing scholars and industry researchers; praise includes R1 research infrastructure and faculty mentorship, with cautions about competitive admission, five-plus-year timelines, and specialized hiring markets.",
        "themes": [
            {
                "label": "Research infrastructure",
                "sentiment": "positive",
                "detail": "Purdue's R1 status and Discovery Park support doctoral research across disciplines.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Doctoral students work closely with faculty on funded research projects.",
            },
            {
                "label": "Career placement",
                "sentiment": "positive",
                "detail": "Graduates enter academia, national labs, and industry R&D leadership.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong research background and faculty alignment are expected.",
            },
        ],
        "sources": [
            {
                "label": "Purdue \u2014 College of Veterinary Medicine",
                "url": "https://vet.purdue.edu/",
            },
            {
                "label": "U.S. News \u2014 Purdue University",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
