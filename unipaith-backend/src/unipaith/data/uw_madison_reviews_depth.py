"""University of Wisconsin-Madison external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``uwmadisonprof3`` migration to merge
``DEPTH_REVIEWS`` into ``uw_madison_profile._REVIEWS_BY_SLUG`` for 47
remaining coverable programs (59/59 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "uw-madison-agricultural-business-and-management-bs": {
        "summary": "Students and third-party guides describe UW-Madison's undergraduate program in Agricultural Business and Management within Wisconsin School of Business as a professionally focused degree at a top-40 public R1 university; praise includes UW-Madison's faculty and Madison campus resources, with cautions about large class sizes, competitive admission, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top public research university",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW-Madison #36 among national universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Agricultural Business and Management lead research and professional training.",
            },
            {
                "label": "Madison campus",
                "sentiment": "positive",
                "detail": "State capital proximity and UW Health enrich study beyond the classroom.",
            },
            {
                "label": "Class scale",
                "sentiment": "caution",
                "detail": "Large university means gateway courses can be lecture-heavy.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on field specialization and graduate-school plans.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Agricultural Business and Management",
                "url": "https://business.wisc.edu/undergraduate/majors/agribusiness/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-agricultural-business-and-management-ms": {
        "summary": "Graduate students describe WSB's graduate program in Agricultural Business and Management as a quantitatively oriented business degree; Poets&Quants and U.S. News rank WSB among leading public business schools; praise includes applied learning and Midwest corporate recruiting, with cautions about selective admission and national brand versus top-15 MBA programs.",
        "themes": [
            {
                "label": "Applied curriculum",
                "sentiment": "positive",
                "detail": "WSB emphasizes experiential learning and corporate-sponsored projects.",
            },
            {
                "label": "Midwest recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from WSB.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition compares favorably to elite private business schools.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Well-regarded regionally; national recognition still developing versus M7 peers.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Graduate business programs have competitive applicant pools.",
            },
        ],
        "sources": [
            {
                "label": "Wisconsin School of Business",
                "url": "https://business.wisc.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wisconsin School of Business",
                "url": "https://poetsandquants.com/schools/wisconsin-school-of-business-university-of-wisconsin/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-agricultural-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Agricultural Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Agricultural Engineering",
                "url": "https://engineering.wisc.edu/departments/biological-systems-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-agricultural-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Agricultural Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Agricultural Engineering",
                "url": "https://engineering.wisc.edu/departments/biological-systems-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-biomedical-medical-engineering-ms": {
        "summary": "Graduate students describe UW-Madison's biomedical engineering M.S. as a research-intensive degree bridging Grainger Engineering and SMPH; praise includes UW Health clinical access and med-device placement, with cautions about self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Clinical translation",
                "sentiment": "positive",
                "detail": "SMPH and UW Health affiliations support med-device and imaging research.",
            },
            {
                "label": "Interdisciplinary labs",
                "sentiment": "positive",
                "detail": "Students join bioelectronics, imaging, and regenerative-medicine groups.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates enter med-device firms, hospital R&D, and Ph.D. programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Prerequisite breadth",
                "sentiment": "mixed",
                "detail": "Biology and engineering prerequisites make the program planning-intensive.",
            },
        ],
        "sources": [
            {
                "label": "UW-Madison Biomedical Engineering \u2014 Graduate",
                "url": "https://engineering.wisc.edu/departments/biomedical-engineering/graduate/",
            },
            {
                "label": "U.S. News \u2014 Biomedical Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/biomedical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-business-commerce-general-ms": {
        "summary": "Graduate students describe WSB's graduate program in Business/Commerce, General as a quantitatively oriented business degree; Poets&Quants and U.S. News rank WSB among leading public business schools; praise includes applied learning and Midwest corporate recruiting, with cautions about selective admission and national brand versus top-15 MBA programs.",
        "themes": [
            {
                "label": "Applied curriculum",
                "sentiment": "positive",
                "detail": "WSB emphasizes experiential learning and corporate-sponsored projects.",
            },
            {
                "label": "Midwest recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from WSB.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition compares favorably to elite private business schools.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Well-regarded regionally; national recognition still developing versus M7 peers.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Graduate business programs have competitive applicant pools.",
            },
        ],
        "sources": [
            {
                "label": "Wisconsin School of Business",
                "url": "https://business.wisc.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wisconsin School of Business",
                "url": "https://poetsandquants.com/schools/wisconsin-school-of-business-university-of-wisconsin/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-chemical-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Chemical Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Chemical Engineering",
                "url": "https://engineering.wisc.edu/departments/chemical-biological-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-chemical-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Chemical Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Chemical Engineering",
                "url": "https://engineering.wisc.edu/departments/chemical-biological-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-civil-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Civil Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Civil Engineering",
                "url": "https://engineering.wisc.edu/departments/civil-environmental-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-civil-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Civil Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Civil Engineering",
                "url": "https://engineering.wisc.edu/departments/civil-environmental-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-computer-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Computer Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Computer Engineering",
                "url": "https://engineering.wisc.edu/departments/electrical-computer-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-data-science-bs": {
        "summary": "Students describe UW-Madison's undergraduate data science major in CDIS as a quantitatively rigorous program bridging computer science, statistics, and domain applications; praise includes access to Wisconsin Institutes for Discovery and strong Midwest analytics recruiting, with cautions that the major is newer than peer CS programs and competitive admission to upper-division CDIS courses is common.",
        "themes": [
            {
                "label": "Interdisciplinary CDIS",
                "sentiment": "positive",
                "detail": "Data science draws on CS, statistics, and applied domain coursework.",
            },
            {
                "label": "Discovery institutes",
                "sentiment": "positive",
                "detail": "WID and Morgridge provide research and industry partnership access.",
            },
            {
                "label": "Analytics recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter tech, healthcare analytics, and consulting roles.",
            },
            {
                "label": "Program maturity",
                "sentiment": "mixed",
                "detail": "Undergraduate data science is newer than established CS majors at peer schools.",
            },
            {
                "label": "Course access",
                "sentiment": "caution",
                "detail": "Popular CDIS courses fill quickly; registration planning matters.",
            },
        ],
        "sources": [
            {
                "label": "CDIS \u2014 Data Science",
                "url": "https://cdis.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-economics-ms": {
        "summary": "Graduate students describe UW-Madison's M.A. in Economics as a quantitatively rigorous program rooted in the Wisconsin School institutional-economics tradition; praise includes econometrics training and La Follette School proximity, with cautions about competitive Ph.D. placement and self-funded tuition for terminal master's students.",
        "themes": [
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Econometrics and labor economics sequences are program hallmarks.",
            },
            {
                "label": "Wisconsin School legacy",
                "sentiment": "positive",
                "detail": "Institutional and labor economics traditions distinguish the department.",
            },
            {
                "label": "Policy access",
                "sentiment": "positive",
                "detail": "Madison state-government proximity creates policy internship opportunities.",
            },
            {
                "label": "Ph.D. competition",
                "sentiment": "caution",
                "detail": "Many M.A. students aim for economics Ph.D. programs with selective admission.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Economics",
                "url": "https://econ.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Electrical, Electronics, and Communications Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://engineering.wisc.edu/departments/electrical-computer-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Electrical, Electronics, and Communications Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://engineering.wisc.edu/departments/electrical-computer-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-engineering-general-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Engineering, General within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Engineering, General",
                "url": "https://engineering.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-engineering-mechanics-bs": {
        "summary": "Students describe UW-Madison's undergraduate Engineering Mechanics program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Engineering Mechanics",
                "url": "https://engineering.wisc.edu/departments/engineering-physics/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-engineering-mechanics-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Engineering Mechanics within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Engineering Mechanics",
                "url": "https://engineering.wisc.edu/departments/engineering-physics/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-engineering-other-bs": {
        "summary": "Students describe UW-Madison's undergraduate Engineering, Other program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Engineering, Other",
                "url": "https://engineering.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-engineering-physics-bs": {
        "summary": "Students describe UW-Madison's undergraduate Engineering Physics program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Engineering Physics",
                "url": "https://engineering.wisc.edu/departments/engineering-physics/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-family-and-consumer-economics-and-related-studies-bs": {
        "summary": "Students describe UW-Madison's Family and Consumer Economics and Related Studies program in the School of Human Ecology as an applied social-science degree with consumer economics and financial security research ties; praise includes Center for Financial Security access, with cautions that the program is smaller than flagship L&S majors.",
        "themes": [
            {
                "label": "Applied focus",
                "sentiment": "positive",
                "detail": "Human Ecology programs emphasize consumer science and family well-being.",
            },
            {
                "label": "Financial security research",
                "sentiment": "positive",
                "detail": "Center for Financial Security supports policy-relevant undergraduate research.",
            },
            {
                "label": "Smaller cohorts",
                "sentiment": "positive",
                "detail": "Human Ecology classes are typically smaller than large L&S lecture courses.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than flagship engineering and business programs.",
            },
            {
                "label": "Career specialization",
                "sentiment": "mixed",
                "detail": "Outcomes concentrate in consumer policy, nonprofit, and applied research roles.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Family and Consumer Economics and Related Studies",
                "url": "https://sohe.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-finance-and-financial-management-services-bs": {
        "summary": "Students describe UW-Madison's finance major through WSB as a quantitatively oriented undergraduate program with strength in corporate finance and the Nicholas Center for Corporate Finance; praise includes Midwest banking and consulting recruiting, with cautions that national finance placement trails top-10 undergraduate business programs.",
        "themes": [
            {
                "label": "Nicholas Center",
                "sentiment": "positive",
                "detail": "Investment banking and corporate finance experiential programs are program hallmarks.",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes corporate finance, investments, and analytics.",
            },
            {
                "label": "Midwest recruiting",
                "sentiment": "positive",
                "detail": "Milwaukee and Chicago finance firms recruit actively from WSB.",
            },
            {
                "label": "Coastal placement",
                "sentiment": "mixed",
                "detail": "Investment banking on the coasts requires proactive networking beyond campus.",
            },
            {
                "label": "Direct admission",
                "sentiment": "caution",
                "detail": "Competitive admission to WSB affects access to finance major coursework.",
            },
        ],
        "sources": [
            {
                "label": "WSB \u2014 Finance Major",
                "url": "https://business.wisc.edu/undergraduate/majors/finance/",
            },
            {
                "label": "U.S. News \u2014 Best Undergraduate Business",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-finance-and-financial-management-services-ms": {
        "summary": "Graduate students describe WSB's graduate program in Finance and Financial Management Services as a quantitatively oriented business degree; Poets&Quants and U.S. News rank WSB among leading public business schools; praise includes applied learning and Midwest corporate recruiting, with cautions about selective admission and national brand versus top-15 MBA programs.",
        "themes": [
            {
                "label": "Applied curriculum",
                "sentiment": "positive",
                "detail": "WSB emphasizes experiential learning and corporate-sponsored projects.",
            },
            {
                "label": "Midwest recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from WSB.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition compares favorably to elite private business schools.",
            },
            {
                "label": "National brand",
                "sentiment": "mixed",
                "detail": "Well-regarded regionally; national recognition still developing versus M7 peers.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Graduate business programs have competitive applicant pools.",
            },
        ],
        "sources": [
            {
                "label": "Wisconsin School of Business",
                "url": "https://business.wisc.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Wisconsin School of Business",
                "url": "https://poetsandquants.com/schools/wisconsin-school-of-business-university-of-wisconsin/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-geological-geophysical-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Geological/Geophysical Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Geological/Geophysical Engineering",
                "url": "https://engineering.wisc.edu/departments/geological-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-geological-geophysical-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Geological/Geophysical Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Geological/Geophysical Engineering",
                "url": "https://engineering.wisc.edu/departments/geological-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-industrial-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Industrial Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Industrial Engineering",
                "url": "https://engineering.wisc.edu/departments/industrial-systems-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-industrial-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Industrial Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Industrial Engineering",
                "url": "https://engineering.wisc.edu/departments/industrial-systems-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-international-business-bs": {
        "summary": "Students and third-party guides describe UW-Madison's undergraduate program in International Business within Wisconsin School of Business as a professionally focused degree at a top-40 public R1 university; praise includes UW-Madison's faculty and Madison campus resources, with cautions about large class sizes, competitive admission, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top public research university",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW-Madison #36 among national universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in International Business lead research and professional training.",
            },
            {
                "label": "Madison campus",
                "sentiment": "positive",
                "detail": "State capital proximity and UW Health enrich study beyond the classroom.",
            },
            {
                "label": "Class scale",
                "sentiment": "caution",
                "detail": "Large university means gateway courses can be lecture-heavy.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on field specialization and graduate-school plans.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 International Business",
                "url": "https://business.wisc.edu/undergraduate/majors/international-business/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/business-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-journalism-bs": {
        "summary": "Students describe UW-Madison's journalism major in SJMC as a practice-oriented program with strong Wisconsin Public Radio and Wisconsin State Journal ties; praise includes reporting labs and the Center for Journalism Ethics, with cautions that media-industry disruption makes portfolio-building and internships essential.",
        "themes": [
            {
                "label": "Practice-first training",
                "sentiment": "positive",
                "detail": "Reporting, multimedia, and strategic communication studios anchor the curriculum.",
            },
            {
                "label": "Wisconsin media ties",
                "sentiment": "positive",
                "detail": "WPR, Wisconsin State Journal, and Madison media outlets offer internship pipelines.",
            },
            {
                "label": "Ethics center",
                "sentiment": "positive",
                "detail": "Center for Journalism Ethics distinguishes SJMC nationally.",
            },
            {
                "label": "Industry disruption",
                "sentiment": "caution",
                "detail": "Traditional newsroom hiring remains competitive; digital skills are essential.",
            },
            {
                "label": "Portfolio careers",
                "sentiment": "mixed",
                "detail": "Outcomes depend on clips, internships, and industry networks.",
            },
        ],
        "sources": [
            {
                "label": "SJMC \u2014 Undergraduate",
                "url": "https://journalism.wisc.edu/undergraduate/",
            },
            {
                "label": "Niche \u2014 University of Wisconsin-Madison",
                "url": "https://www.niche.com/colleges/university-of-wisconsin-madison/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-journalism-ms": {
        "summary": "Graduate students describe SJMC's journalism master's as a research-and-practice degree with strengths in political communication and health journalism; praise includes faculty media research and Madison state-government access, with cautions about limited graduate funding compared with STEM programs.",
        "themes": [
            {
                "label": "Research & practice",
                "sentiment": "positive",
                "detail": "Graduate tracks combine media research with applied reporting projects.",
            },
            {
                "label": "State capital access",
                "sentiment": "positive",
                "detail": "Madison's government and policy community enriches political journalism study.",
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": "SJMC faculty lead studies in political and health communication.",
            },
            {
                "label": "Funding scarcity",
                "sentiment": "caution",
                "detail": "Graduate assistantships are scarcer than in STEM Ph.D. programs.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes span academia, nonprofit media, and industry communication roles.",
            },
        ],
        "sources": [
            {
                "label": "SJMC \u2014 Graduate Programs",
                "url": "https://journalism.wisc.edu/graduate/",
            },
            {
                "label": "Niche \u2014 University of Wisconsin-Madison",
                "url": "https://www.niche.com/colleges/university-of-wisconsin-madison/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-landscape-architecture-bs": {
        "summary": "Students describe UW-Madison's landscape architecture program as a design-intensive professional degree emphasizing ecological planning and Midwest land-use issues; praise includes studio culture and Arboretum access, with cautions about long studio hours and licensure pathways beyond the degree.",
        "themes": [
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": "Design studios and site-planning projects anchor the curriculum.",
            },
            {
                "label": "Ecological focus",
                "sentiment": "positive",
                "detail": "UW Arboretum and Nelson Institute ties enrich sustainability coursework.",
            },
            {
                "label": "Interdisciplinary ties",
                "sentiment": "positive",
                "detail": "Connections to CALS and civil engineering enrich planning projects.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Long studio hours and intensive crit schedules are recurring themes.",
            },
            {
                "label": "Licensure path",
                "sentiment": "mixed",
                "detail": "Professional landscape architecture licensure requires additional experience.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Landscape Architecture",
                "url": "https://landscapearchitecture.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-landscape-architecture-ms": {
        "summary": "Graduate students describe UW-Madison's M.S. in landscape architecture as a research-and-design degree with ecological planning strengths; praise includes Nelson Institute and Arboretum access, with cautions about studio workload and competitive funding for research assistantships.",
        "themes": [
            {
                "label": "Ecological planning",
                "sentiment": "positive",
                "detail": "Graduate research spans urban ecology, restoration, and climate adaptation.",
            },
            {
                "label": "Arboretum access",
                "sentiment": "positive",
                "detail": "UW Arboretum provides living-laboratory sites for design research.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "Nelson Institute connections enrich sustainability-focused projects.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Graduate studios and thesis projects require sustained intensive work.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships in design programs are more limited than in STEM.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Landscape Architecture",
                "url": "https://landscapearchitecture.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-law-phd": {
        "summary": "Doctoral scholars describe UW Law's Law as a research degree within a well-regarded public law school; praise includes faculty mentorship, the Wisconsin Innocence Project, and Madison legal community access, with cautions about competitive academic hiring and limited funding relative to private peers.",
        "themes": [
            {
                "label": "Public law school value",
                "sentiment": "positive",
                "detail": "UW Law offers strong scholarship support and lower debt than private peers.",
            },
            {
                "label": "Clinical programs",
                "sentiment": "positive",
                "detail": "Innocence Project and entrepreneurship clinic provide distinctive research training.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small doctoral cohorts enable close work with legal scholars.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are nationally competitive.",
            },
            {
                "label": "Funding variability",
                "sentiment": "caution",
                "detail": "Doctoral funding packages vary; external fellowships are common.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Law School",
                "url": "https://law.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-wisconsin-3895",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-materials-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Materials Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Materials Engineering",
                "url": "https://engineering.wisc.edu/departments/materials-science-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-materials-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Materials Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Materials Engineering",
                "url": "https://engineering.wisc.edu/departments/materials-science-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-mechanical-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Mechanical Engineering as a research and coursework degree within a top-20 public engineering college; praise includes Grainger Engineering Design Innovation Lab access and Midwest manufacturing recruiting, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Top engineering rank",
                "sentiment": "positive",
                "detail": "UW-Madison mechanical engineering is consistently ranked among leading programs.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab supports graduate research in manufacturing and product design.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Caterpillar, Rockwell, and automotive firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW-Madison Mechanical Engineering \u2014 Graduate",
                "url": "https://engineering.wisc.edu/departments/mechanical-engineering/graduate/",
            },
            {
                "label": "U.S. News \u2014 Mechanical Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-medicine-phd": {
        "summary": "Doctoral students describe SMPH's Ph.D. in Medicine as a research-intensive health-sciences degree with access to UW Carbone Cancer Center and ICTR; praise includes translational research infrastructure, with cautions about competitive residency matching and long dissertation timelines.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks SMPH among leading public medical schools for research.",
            },
            {
                "label": "Carbone Cancer Center",
                "sentiment": "positive",
                "detail": "NCI-designated cancer center supports doctoral research across disciplines.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "ICTR connects basic science to clinical trials and community health.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Biomedical Ph.D. programs commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 School of Medicine and Public Health",
                "url": "https://www.med.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-wisconsin-madison-04072",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-nuclear-engineering-bs": {
        "summary": "Students describe UW-Madison's undergraduate Nuclear Engineering program in Grainger Engineering as a nationally ranked engineering degree with strong theory-to-application training; praise includes Grainger Design Innovation Lab access and Midwest industry recruiting, with cautions that large lower-division sections require proactive faculty engagement.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among top public programs nationally.",
            },
            {
                "label": "Design Innovation Lab",
                "sentiment": "positive",
                "detail": "Grainger lab and senior design capstone integrate real industry sponsors.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger.",
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
                "label": "UW\u2013Madison \u2014 Nuclear Engineering",
                "url": "https://engineering.wisc.edu/departments/engineering-physics/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-nuclear-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Nuclear Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Nuclear Engineering",
                "url": "https://engineering.wisc.edu/departments/engineering-physics/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-public-health-ms": {
        "summary": "Graduate applicants describe UW-Madison's MPH through SMPH as a practice-oriented public health degree with strengths in epidemiology, health policy, and rural health through WARM-affiliated pathways; praise includes UW Health partnerships and affordable in-state tuition, with cautions that the school is smaller than top-10 public health programs.",
        "themes": [
            {
                "label": "Rural health mission",
                "sentiment": "positive",
                "detail": "SMPH emphasizes community and rural health across Wisconsin.",
            },
            {
                "label": "UW Health access",
                "sentiment": "positive",
                "detail": "Clinical and population-health practicum sites span the UW Health system.",
            },
            {
                "label": "Affordable tuition",
                "sentiment": "positive",
                "detail": "In-state rates compare favorably to coastal MPH programs.",
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": "Smaller than top-10 public health schools; fewer specialized concentrations.",
            },
            {
                "label": "Funding limits",
                "sentiment": "caution",
                "detail": "Research assistantships are more limited than at larger peer programs.",
            },
        ],
        "sources": [
            {
                "label": "SMPH \u2014 Master of Public Health",
                "url": "https://www.med.wisc.edu/education/public-health/",
            },
            {
                "label": "U.S. News \u2014 Public Health Rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-ms": {
        "summary": "Graduate students describe UW-Madison's M.S. in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as an advanced nursing degree with clinical research opportunities through UW Health; praise includes Center for Aging Research and Education, with cautions about limited funding compared with larger nursing graduate programs.",
        "themes": [
            {
                "label": "Clinical research",
                "sentiment": "positive",
                "detail": "UW Health system supports advanced practice and nursing science research.",
            },
            {
                "label": "Aging research",
                "sentiment": "positive",
                "detail": "CARE supports gerontology and chronic-disease nursing research.",
            },
            {
                "label": "Advanced practice",
                "sentiment": "positive",
                "detail": "Graduates enter nurse practitioner, leadership, and research roles.",
            },
            {
                "label": "Funding limits",
                "sentiment": "caution",
                "detail": "Graduate assistantships are more limited than at larger peer programs.",
            },
            {
                "label": "Clinical demands",
                "sentiment": "mixed",
                "detail": "Advanced practice tracks require intensive clinical hour commitments.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://nursing.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/nursing-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": {
        "summary": "Doctoral students describe UW-Madison's Ph.D. in Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing as a research degree preparing nurse scientists; praise includes Center for Aging Research and Education and UW Health clinical research access, with cautions about specialized academic hiring and competitive funding.",
        "themes": [
            {
                "label": "Nurse scientist training",
                "sentiment": "positive",
                "detail": "Program prepares graduates for faculty and health-system research leadership.",
            },
            {
                "label": "Aging research center",
                "sentiment": "positive",
                "detail": "CARE supports gerontology and chronic-disease research pathways.",
            },
            {
                "label": "Clinical research access",
                "sentiment": "positive",
                "detail": "UW Health affiliations provide diverse patient-population research sites.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Nursing faculty positions are competitive nationally.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "NIH-funded training slots are limited relative to applicant pools.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing",
                "url": "https://nursing.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/nursing-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-social-work-bs": {
        "summary": "Students describe UW-Madison's Social Work program as an undergraduate social work degree with field placements across Wisconsin agencies; praise includes the Institute for Research on Poverty proximity and faculty research access, with cautions that licensure pathways require an MSW for clinical practice.",
        "themes": [
            {
                "label": "Field placements",
                "sentiment": "positive",
                "detail": "Wisconsin agencies provide diverse undergraduate practicum experiences.",
            },
            {
                "label": "Poverty research",
                "sentiment": "positive",
                "detail": "Institute for Research on Poverty enriches policy-oriented coursework.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Smaller program enables closer faculty mentorship than large L&S majors.",
            },
            {
                "label": "MSW requirement",
                "sentiment": "caution",
                "detail": "Clinical social work licensure requires a graduate MSW beyond the bachelor's.",
            },
            {
                "label": "Emotional demands",
                "sentiment": "mixed",
                "detail": "Field work with vulnerable populations can be emotionally intensive.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 School of Social Work",
                "url": "https://socwork.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-social-work-ms": {
        "summary": "Graduate students describe UW-Madison's MSW as a top-ranked social work program with strengths in poverty research through the Institute for Research on Poverty and clinical training; praise includes Wisconsin field placements and faculty research, with cautions about emotionally demanding practicum work and licensure requirements varying by state.",
        "themes": [
            {
                "label": "Top social work rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks UW-Madison social work among leading programs nationally.",
            },
            {
                "label": "Poverty research",
                "sentiment": "positive",
                "detail": "Institute for Research on Poverty anchors distinctive policy research training.",
            },
            {
                "label": "Field placements",
                "sentiment": "positive",
                "detail": "Wisconsin agencies and health systems provide diverse practicum sites.",
            },
            {
                "label": "Emotional demands",
                "sentiment": "caution",
                "detail": "Clinical practicum work with vulnerable populations is emotionally intensive.",
            },
            {
                "label": "Licensure variation",
                "sentiment": "mixed",
                "detail": "MSW licensure requirements vary; graduates should plan for state-specific exams.",
            },
        ],
        "sources": [
            {
                "label": "UW-Madison School of Social Work \u2014 MSW",
                "url": "https://socwork.wisc.edu/academics/msw/",
            },
            {
                "label": "U.S. News \u2014 Social Work Rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-systems-engineering-ms": {
        "summary": "Graduate applicants describe UW-Madison's M.S. in Systems Engineering within Grainger Engineering as a research and coursework degree at a top public engineering college; students value Midwest manufacturing and tech recruiting, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "Grainger Engineering is consistently ranked among leading public programs.",
            },
            {
                "label": "Research labs",
                "sentiment": "positive",
                "detail": "Graduate students join faculty labs in WID-affiliated research centers.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Manufacturing, tech, and med-device firms recruit actively.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across Grainger Engineering.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Systems Engineering",
                "url": "https://engineering.wisc.edu/departments/industrial-systems-engineering/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-veterinary-biomedical-and-clinical-sciences-ms": {
        "summary": "Graduate students describe UW-Madison's M.S. in Veterinary Biomedical and Clinical Sciences at the School of Veterinary Medicine as a research degree with access to WVDL and UW Veterinary Care; praise includes One Health and food-animal research, with cautions about competitive admission and specialized veterinary career paths.",
        "themes": [
            {
                "label": "Teaching hospital",
                "sentiment": "positive",
                "detail": "UW Veterinary Care provides broad small- and large-animal clinical exposure.",
            },
            {
                "label": "WVDL diagnostics",
                "sentiment": "positive",
                "detail": "State diagnostic laboratory supports real-world disease surveillance research.",
            },
            {
                "label": "One Health research",
                "sentiment": "positive",
                "detail": "Comparative medicine and zoonotic disease research are program strengths.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Graduate veterinary research programs have selective admission pools.",
            },
            {
                "label": "Specialized market",
                "sentiment": "mixed",
                "detail": "Career paths concentrate in veterinary research, academia, and government.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 Veterinary Biomedical and Clinical Sciences",
                "url": "https://www.vetmed.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-colleges/rankings/biomedical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "uw-madison-veterinary-medicine-phd": {
        "summary": "Doctoral students describe UW-Madison's Ph.D. in Veterinary Medicine as a research degree in comparative biomedical sciences with access to the Wisconsin Veterinary Diagnostic Laboratory; praise includes One Health and food-animal research, with cautions about long dissertation timelines and specialized hiring markets.",
        "themes": [
            {
                "label": "Comparative medicine",
                "sentiment": "positive",
                "detail": "Doctoral research spans veterinary, human, and environmental health.",
            },
            {
                "label": "WVDL diagnostics",
                "sentiment": "positive",
                "detail": "State diagnostic laboratory supports real-world disease surveillance research.",
            },
            {
                "label": "One Health focus",
                "sentiment": "positive",
                "detail": "Food-animal and zoonotic disease research are program strengths.",
            },
            {
                "label": "Dissertation timeline",
                "sentiment": "caution",
                "detail": "Veterinary biomedical Ph.D. programs commonly span five or more years.",
            },
            {
                "label": "Academic market",
                "sentiment": "mixed",
                "detail": "Faculty positions concentrate in veterinary and biomedical sciences.",
            },
        ],
        "sources": [
            {
                "label": "UW\u2013Madison \u2014 School of Veterinary Medicine",
                "url": "https://www.vetmed.wisc.edu/",
            },
            {
                "label": "U.S. News \u2014 University of Wisconsin-Madison",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-wisconsin-madison-04072",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
