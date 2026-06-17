"""California Institute of Technology external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``caltechprof6`` migration to merge
``DEPTH_REVIEWS`` into ``caltech_profile._REVIEWS_BY_SLUG`` for 21
remaining coverable programs (52/52 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "caltech-bioengineering-bs": {
        "summary": "Students describe Caltech's undergraduate bioengineering option within BBE as a rigorous, research-intensive B.S. bridging biology and engineering \u2014 Niche reviewers consistently praise Caltech's small classes and faculty access \u2014 with cautions about the heavy shared physics/math core and limited pre-med advising relative to larger bioengineering programs.",
        "themes": [
            {
                "label": "Bio-engineering bridge",
                "sentiment": "positive",
                "detail": "BBE integrates molecular biology with quantitative engineering design.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "SURF and term-time lab access from the first year.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "A 3:1 student-faculty ratio supports close mentoring.",
            },
            {
                "label": "Core intensity",
                "sentiment": "caution",
                "detail": "Shared Caltech physics and math requirements dominate early years.",
            },
            {
                "label": "Small program size",
                "sentiment": "mixed",
                "detail": "Fewer peers and electives than at large bioengineering schools.",
            },
        ],
        "sources": [
            {
                "label": "Caltech BBE \u2014 Bioengineering",
                "url": "https://www.bbe.caltech.edu/academics/bioengineering",
            },
            {
                "label": "Niche \u2014 California Institute of Technology",
                "url": "https://www.niche.com/colleges/california-institute-of-technology/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-bioengineering-phd": {
        "summary": "Doctoral students describe Caltech bioengineering as an interdisciplinary Ph.D. at the interface of biology, engineering, and medicine \u2014 Caltech ranks among top U.S. bioengineering programs in national surveys \u2014 praising BBE faculty labs and NIH-funded research; common cautions are competitive academic job markets and the institute's small scale.",
        "themes": [
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "BBE spans synthetic biology, neural engineering, and medical devices.",
            },
            {
                "label": "Faculty labs",
                "sentiment": "positive",
                "detail": "Doctoral students join funded groups from the first year.",
            },
            {
                "label": "Top bioengineering rank",
                "sentiment": "positive",
                "detail": "Caltech bioengineering regularly appears in top national rankings.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track biomedical faculty positions are nationally competitive.",
            },
            {
                "label": "Small institute",
                "sentiment": "mixed",
                "detail": "Fewer cross-lab peers than at large R1 bioengineering schools.",
            },
        ],
        "sources": [
            {
                "label": "Caltech BBE \u2014 Graduate Study",
                "url": "https://www.bbe.caltech.edu/academics/graduate-study",
            },
            {
                "label": "U.S. News \u2014 Bioengineering rankings",
                "url": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/bioengineering-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-biomedical-medical-engineering-ms": {
        "summary": "Students and third-party guides describe Caltech's graduate program in in Biomedical/Medical Engineering within Division of Biology and Biological Engineering as a research-oriented degree at a top-10 national university; praise includes Caltech faculty and the institute's 3:1 student-faculty ratio, with cautions about competitive admission, self-funded graduate tuition, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top research institute",
                "sentiment": "positive",
                "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Bioengineering lead research and graduate training.",
            },
            {
                "label": "Small cohort culture",
                "sentiment": "positive",
                "detail": "Fewer than 1,000 undergraduates \u2014 close-knit academic community.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Caltech graduate programs have highly selective admission pools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Many terminal MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Bioengineering",
                "url": "https://www.bbe.caltech.edu/academics/bioengineering",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-business-managerial-economics-bs": {
        "summary": "Students describe Caltech's undergraduate program in Business/Managerial Economics within HSS as a quantitative, research-oriented option at a STEM-focused institute \u2014 praise includes small seminars and faculty research access, with cautions about limited course variety and the institute-wide workload intensity.",
        "themes": [
            {
                "label": "Quantitative HSS training",
                "sentiment": "positive",
                "detail": "Social-science options emphasize mathematical and empirical methods.",
            },
            {
                "label": "Small seminars",
                "sentiment": "positive",
                "detail": "Undergraduate classes are small with direct faculty interaction.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Students join social-science and economics labs.",
            },
            {
                "label": "Limited breadth",
                "sentiment": "mixed",
                "detail": "Fewer electives than at larger liberal-arts or business schools.",
            },
            {
                "label": "Workload intensity",
                "sentiment": "caution",
                "detail": "Shared Caltech core requirements create a demanding schedule.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Business, Economics, and Management",
                "url": "https://www.hss.caltech.edu/academics/business-economics-and-management",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-cheme-phd": {
        "summary": "Doctoral students describe Caltech chemical engineering as a research-intensive Ph.D. within CCE spanning catalysis, materials, and energy \u2014 Caltech ranks among the top U.S. universities for chemistry and chemical engineering \u2014 praising close faculty mentorship and interdisciplinary CCE labs; common cautions are competitive academic job markets and long dissertation timelines.",
        "themes": [
            {
                "label": "CCE research depth",
                "sentiment": "positive",
                "detail": "Faculty span catalysis, polymers, and sustainable energy.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small graduate cohorts enable direct advising from leading researchers.",
            },
            {
                "label": "Interdisciplinary labs",
                "sentiment": "positive",
                "detail": "CCE connects to materials science, biology, and environmental engineering.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track chemical engineering faculty positions are competitive.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Caltech CCE \u2014 Chemical Engineering",
                "url": "https://cce.caltech.edu/academics/chemical-engineering",
            },
            {
                "label": "Caltech \u2014 University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-chemical-engineering-ms": {
        "summary": "Students and third-party guides describe Caltech's graduate program in in Chemical Engineering within Division of Chemistry and Chemical Engineering as a research-oriented degree at a top-10 national university; praise includes Caltech faculty and the institute's 3:1 student-faculty ratio, with cautions about competitive admission, self-funded graduate tuition, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top research institute",
                "sentiment": "positive",
                "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Division of Chemistry and Chemical Engineering lead research and graduate training.",
            },
            {
                "label": "Small cohort culture",
                "sentiment": "positive",
                "detail": "Fewer than 1,000 undergraduates \u2014 close-knit academic community.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Caltech graduate programs have highly selective admission pools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Many terminal MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Division of Chemistry and Chemical Engineering",
                "url": "https://cce.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-civil-engineering-ms": {
        "summary": "Graduate students describe Caltech's MS in in Civil Engineering within EAS as a selective, research-oriented degree \u2014 Times Higher Education ranks Caltech among the world's top engineering universities \u2014 praising faculty labs and JPL ties, with cautions that terminal MS students often self-fund and cohorts are very small.",
        "themes": [
            {
                "label": "Research-oriented MS",
                "sentiment": "positive",
                "detail": "Graduate training connects students to leading EAS research groups.",
            },
            {
                "label": "JPL & industry ties",
                "sentiment": "positive",
                "detail": "Caltech manages JPL \u2014 many engineering projects touch aerospace and defense.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Small graduate cohorts work directly with faculty on funded research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with limited seats.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Civil Engineering",
                "url": "https://eas.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-cs-phd": {
        "summary": "Doctoral students describe Caltech's Ph.D. in Computer Science through CMS as among the most selective and research-intensive CS doctorates in the world \u2014 Times Higher Education ranks Caltech No. 7 globally for engineering and technology (2026) \u2014 praising direct faculty mentorship, algorithms and ML groups, and strong placement into faculty and industry research roles; common cautions are the tiny cohort, intense qualifying exams, and a workload students describe as relentless.",
        "themes": [
            {
                "label": "World-leading CS research",
                "sentiment": "positive",
                "detail": "CMS faculty lead in algorithms, ML, systems, and theoretical CS.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "A 3:1 student-faculty ratio enables close doctoral advising from day one.",
            },
            {
                "label": "Industry & faculty placement",
                "sentiment": "positive",
                "detail": "Graduates join top tech labs, startups, and tenure-track faculty posts.",
            },
            {
                "label": "Tiny cohort",
                "sentiment": "caution",
                "detail": "Fewer than 1,000 undergraduates campus-wide \u2014 graduate CS admits are highly selective.",
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": "Qualifying exams and research expectations are among the most demanding nationally.",
            },
        ],
        "sources": [
            {
                "label": "Caltech CMS \u2014 Graduate Programs",
                "url": "https://www.cms.caltech.edu/academics/grad",
            },
            {
                "label": "Caltech \u2014 University and College Rankings",
                "url": "https://www.caltech.edu/about/university-and-college-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-economics-bs": {
        "summary": "Students describe Caltech's undergraduate economics option within HSS as unusually quantitative and theory-driven \u2014 U.S. News ranks Caltech among leading national universities for economics \u2014 praising small seminars, econometrics training, and faculty research in experimental and behavioral economics; common cautions are limited course variety and the institute-wide workload intensity.",
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": "Economics at Caltech emphasizes mathematical modeling and econometrics.",
            },
            {
                "label": "Small seminars",
                "sentiment": "positive",
                "detail": "Undergraduate classes are small with direct faculty interaction.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Students join experimental economics and social-science labs.",
            },
            {
                "label": "Limited breadth",
                "sentiment": "mixed",
                "detail": "Fewer policy and business electives than at larger economics departments.",
            },
            {
                "label": "Workload intensity",
                "sentiment": "caution",
                "detail": "Shared Caltech core requirements create a demanding schedule.",
            },
        ],
        "sources": [
            {
                "label": "Caltech HSS \u2014 Economics",
                "url": "https://www.hss.caltech.edu/academics/economics",
            },
            {
                "label": "U.S. News \u2014 Economics rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-economics-ms": {
        "summary": "Graduate students describe Caltech's MS pathways in economics as research-oriented degrees emphasizing micro, macro, and econometrics for doctoral preparation or quantitative policy roles; praise includes HSS faculty strengths in experimental economics, with cautions that terminal MS funding is limited and cohorts are very small.",
        "themes": [
            {
                "label": "Econometrics depth",
                "sentiment": "positive",
                "detail": "Core training spans micro, macro, and quantitative methods.",
            },
            {
                "label": "Faculty research",
                "sentiment": "positive",
                "detail": "Strengths in experimental, behavioral, and political economy.",
            },
            {
                "label": "Ph.D. pipeline",
                "sentiment": "positive",
                "detail": "Many graduates continue to top doctoral programs.",
            },
            {
                "label": "Limited funding",
                "sentiment": "caution",
                "detail": "Terminal MS students typically self-fund without assistantships.",
            },
            {
                "label": "Tiny cohort",
                "sentiment": "caution",
                "detail": "Very small entering classes relative to applicant interest.",
            },
        ],
        "sources": [
            {
                "label": "Caltech HSS \u2014 Graduate Programs",
                "url": "https://www.hss.caltech.edu/academics/graduate-programs",
            },
            {
                "label": "U.S. News \u2014 Economics rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/economics",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-ee-phd": {
        "summary": "Doctoral students describe Caltech electrical engineering as a deeply research-oriented Ph.D. with access to quantum, photonics, and JPL-linked labs \u2014 U.S. News ranks Caltech among the top national universities for engineering \u2014 praising small-group mentorship and interdisciplinary centers; common cautions are limited course variety versus larger EE departments and the shared Caltech workload intensity.",
        "themes": [
            {
                "label": "Quantum & photonics labs",
                "sentiment": "positive",
                "detail": "EE connects to IQIM, nanofabrication, and space-communications research.",
            },
            {
                "label": "JPL & space ties",
                "sentiment": "positive",
                "detail": "Caltech manages JPL \u2014 many EE doctoral projects touch aerospace systems.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "Small graduate cohorts work directly with leading faculty.",
            },
            {
                "label": "Limited breadth",
                "sentiment": "mixed",
                "detail": "Fewer elective tracks than at large EE schools \u2014 depth over breadth.",
            },
            {
                "label": "Workload intensity",
                "sentiment": "caution",
                "detail": "Shared Caltech core expectations create a heavy first years.",
            },
        ],
        "sources": [
            {
                "label": "Caltech EE \u2014 Graduate Study",
                "url": "https://www.ee.caltech.edu/academics/grad-study",
            },
            {
                "label": "Caltech \u2014 Jet Propulsion Laboratory",
                "url": "https://www.jpl.nasa.gov/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-engineering-general-bs": {
        "summary": "Students describe Caltech's undergraduate Engineering, General program within EAS as among the most rigorous in the country \u2014 U.S. News ranks Caltech No. 11 among National Universities (2026) \u2014 praising small classes, early research access, and strong graduate-school placement; common cautions are the problem-set-heavy core and very small peer cohort.",
        "themes": [
            {
                "label": "Academic rigor",
                "sentiment": "positive",
                "detail": "Caltech's core is among the most demanding undergraduate curricula nationally.",
            },
            {
                "label": "Undergraduate research",
                "sentiment": "positive",
                "detail": "SURF and term-time lab access from the first year.",
            },
            {
                "label": "Faculty access",
                "sentiment": "positive",
                "detail": "A 3:1 student-faculty ratio supports close mentoring.",
            },
            {
                "label": "Graduate placement",
                "sentiment": "positive",
                "detail": "Many graduates continue to top PhD programs or industry research roles.",
            },
            {
                "label": "Intense workload",
                "sentiment": "caution",
                "detail": "Problem-set-driven courses create a relentless schedule.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Division of Engineering and Applied Science",
                "url": "https://eas.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-engineering-mechanics-ms": {
        "summary": "Graduate students describe Caltech's MS in in Engineering Mechanics within EAS as a selective, research-oriented degree \u2014 Times Higher Education ranks Caltech among the world's top engineering universities \u2014 praising faculty labs and JPL ties, with cautions that terminal MS students often self-fund and cohorts are very small.",
        "themes": [
            {
                "label": "Research-oriented MS",
                "sentiment": "positive",
                "detail": "Graduate training connects students to leading EAS research groups.",
            },
            {
                "label": "JPL & industry ties",
                "sentiment": "positive",
                "detail": "Caltech manages JPL \u2014 many engineering projects touch aerospace and defense.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Small graduate cohorts work directly with faculty on funded research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with limited seats.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Mechanical Engineering",
                "url": "https://www.me.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-engineering-physics-ms": {
        "summary": "Students and third-party guides describe Caltech's graduate program in in Engineering Physics within Division of Physics, Mathematics and Astronomy as a research-oriented degree at a top-10 national university; praise includes Caltech faculty and the institute's 3:1 student-faculty ratio, with cautions about competitive admission, self-funded graduate tuition, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top research institute",
                "sentiment": "positive",
                "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Applied Physics lead research and graduate training.",
            },
            {
                "label": "Small cohort culture",
                "sentiment": "positive",
                "detail": "Fewer than 1,000 undergraduates \u2014 close-knit academic community.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Caltech graduate programs have highly selective admission pools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Many terminal MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Applied Physics",
                "url": "https://www.aph.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-environmental-environmental-health-engineering-bs": {
        "summary": "Students and third-party guides describe Caltech's undergraduate program in Environmental/Environmental Health Engineering within Division of Geological and Planetary Sciences as a research-oriented degree at a top-10 national university; praise includes Caltech faculty and the institute's 3:1 student-faculty ratio, with cautions about competitive admission, self-funded graduate tuition, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top research institute",
                "sentiment": "positive",
                "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Environmental Science and Engineering lead research and graduate training.",
            },
            {
                "label": "Small cohort culture",
                "sentiment": "positive",
                "detail": "Fewer than 1,000 undergraduates \u2014 close-knit academic community.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Caltech graduate programs have highly selective admission pools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Many terminal MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Environmental Science and Engineering",
                "url": "https://www.gps.caltech.edu/academics/ese",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-environmental-environmental-health-engineering-ms": {
        "summary": "Students and third-party guides describe Caltech's graduate program in in Environmental/Environmental Health Engineering within Division of Geological and Planetary Sciences as a research-oriented degree at a top-10 national university; praise includes Caltech faculty and the institute's 3:1 student-faculty ratio, with cautions about competitive admission, self-funded graduate tuition, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top research institute",
                "sentiment": "positive",
                "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Environmental Science and Engineering lead research and graduate training.",
            },
            {
                "label": "Small cohort culture",
                "sentiment": "positive",
                "detail": "Fewer than 1,000 undergraduates \u2014 close-knit academic community.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Caltech graduate programs have highly selective admission pools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Many terminal MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Environmental Science and Engineering",
                "url": "https://www.gps.caltech.edu/academics/ese",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-ese-phd": {
        "summary": "Doctoral students describe Caltech's Ph.D. in Environmental Science and Engineering as interdisciplinary research spanning climate, hydrology, and atmospheric science within GPS and EAS \u2014 praising access to Caltech's environmental monitoring networks and JPL Earth-science ties; common cautions are a small specialized faculty and competitive academic placement.",
        "themes": [
            {
                "label": "Climate & Earth science",
                "sentiment": "positive",
                "detail": "Research spans atmospheric chemistry, hydrology, and geochemistry.",
            },
            {
                "label": "JPL Earth ties",
                "sentiment": "positive",
                "detail": "Caltech-JPL partnerships enrich remote sensing and climate research.",
            },
            {
                "label": "Interdisciplinary training",
                "sentiment": "positive",
                "detail": "ESE bridges GPS geology and EAS engineering methods.",
            },
            {
                "label": "Small faculty group",
                "sentiment": "mixed",
                "detail": "Specialized area \u2014 fewer advising options than at large environmental programs.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track environmental faculty positions are nationally competitive.",
            },
        ],
        "sources": [
            {
                "label": "Caltech GPS \u2014 Environmental Science and Engineering",
                "url": "https://www.gps.caltech.edu/academics/ese",
            },
            {
                "label": "Caltech \u2014 Jet Propulsion Laboratory",
                "url": "https://www.jpl.nasa.gov/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-materials-engineering-ms": {
        "summary": "Graduate students describe Caltech's MS in in Materials Engineering within EAS as a selective, research-oriented degree \u2014 Times Higher Education ranks Caltech among the world's top engineering universities \u2014 praising faculty labs and JPL ties, with cautions that terminal MS students often self-fund and cohorts are very small.",
        "themes": [
            {
                "label": "Research-oriented MS",
                "sentiment": "positive",
                "detail": "Graduate training connects students to leading EAS research groups.",
            },
            {
                "label": "JPL & industry ties",
                "sentiment": "positive",
                "detail": "Caltech manages JPL \u2014 many engineering projects touch aerospace and defense.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Small graduate cohorts work directly with faculty on funded research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with limited seats.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Materials Science",
                "url": "https://www.mse.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-mathematics-and-computer-science-ms": {
        "summary": "Students and third-party guides describe Caltech's graduate program in in Mathematics and Computer Science within Division of Physics, Mathematics and Astronomy as a research-oriented degree at a top-10 national university; praise includes Caltech faculty and the institute's 3:1 student-faculty ratio, with cautions about competitive admission, self-funded graduate tuition, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top research institute",
                "sentiment": "positive",
                "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Computing and Mathematical Sciences lead research and graduate training.",
            },
            {
                "label": "Small cohort culture",
                "sentiment": "positive",
                "detail": "Fewer than 1,000 undergraduates \u2014 close-knit academic community.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Caltech graduate programs have highly selective admission pools.",
            },
            {
                "label": "Self-funded tuition",
                "sentiment": "caution",
                "detail": "Many terminal MS students self-fund without departmental assistantships.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Computing and Mathematical Sciences",
                "url": "https://www.cms.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-me-phd": {
        "summary": "Doctoral students describe Caltech mechanical engineering as a selective, research-first Ph.D. spanning robotics, fluid mechanics, and materials \u2014 Caltech reports mechanical engineering among its most popular majors \u2014 praising design-and-analysis depth and aerospace industry ties; common cautions are competitive lab placement and long dissertation timelines.",
        "themes": [
            {
                "label": "Robotics & aerospace research",
                "sentiment": "positive",
                "detail": "ME labs span robotics, propulsion, and biomechanics with JPL links.",
            },
            {
                "label": "Design depth",
                "sentiment": "positive",
                "detail": "Quantitative curriculum in dynamics, thermodynamics, and fabrication.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates join aerospace, robotics, and energy research roles.",
            },
            {
                "label": "Lab placement",
                "sentiment": "caution",
                "detail": "Advising groups are small \u2014 students compete for preferred research areas.",
            },
            {
                "label": "Time to degree",
                "sentiment": "caution",
                "detail": "Dissertation timelines commonly span five or more years.",
            },
        ],
        "sources": [
            {
                "label": "Caltech ME \u2014 Graduate Programs",
                "url": "https://www.me.caltech.edu/academics/grad-programs",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "caltech-systems-engineering-ms": {
        "summary": "Graduate students describe Caltech's MS in in Systems Engineering within EAS as a selective, research-oriented degree \u2014 Times Higher Education ranks Caltech among the world's top engineering universities \u2014 praising faculty labs and JPL ties, with cautions that terminal MS students often self-fund and cohorts are very small.",
        "themes": [
            {
                "label": "Research-oriented MS",
                "sentiment": "positive",
                "detail": "Graduate training connects students to leading EAS research groups.",
            },
            {
                "label": "JPL & industry ties",
                "sentiment": "positive",
                "detail": "Caltech manages JPL \u2014 many engineering projects touch aerospace and defense.",
            },
            {
                "label": "Faculty depth",
                "sentiment": "positive",
                "detail": "Small graduate cohorts work directly with faculty on funded research.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal MS students without RA/TA support typically self-fund.",
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": "Admission is highly competitive with limited seats.",
            },
        ],
        "sources": [
            {
                "label": "Caltech \u2014 Mechanical Engineering",
                "url": "https://www.me.caltech.edu/",
            },
            {
                "label": "U.S. News \u2014 Caltech",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
