"""Georgia Institute of Technology external_reviews depth pass.

Depth pass date: 2026-06-18. Consumed by the ``gatechprof2`` migration to merge
``DEPTH_REVIEWS`` into ``georgia_tech_profile._REVIEWS_BY_SLUG`` for 58
remaining coverable programs (62/62 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, the trade press, official employment reports, and reputable student-review communities). Themes summarize common sentiment; they are not individual verbatim quotes or institute endorsements."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "gatech-aerospace-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Aerospace Engineering in the Daniel Guggenheim School as a top-ranked program with strengths in aerodynamics, propulsion, and space systems. Reviewers highlight GTRI ties, NASA and defense recruiting, and the co-op program, while noting a demanding math and physics core and competitive research-lab access.",
        "themes": [
            {
                "label": "Top aerospace program",
                "sentiment": "positive",
                "detail": "Georgia Tech aerospace is consistently ranked among the top U.S. programs by U.S. News.",
            },
            {
                "label": "GTRI and research labs",
                "sentiment": "positive",
                "detail": "Undergraduates access wind tunnels, propulsion labs, and GTRI research partnerships.",
            },
            {
                "label": "Defense and space recruiting",
                "sentiment": "positive",
                "detail": "Graduates place at NASA, major aerospace firms, and defense contractors.",
            },
            {
                "label": "Demanding prerequisites",
                "sentiment": "caution",
                "detail": "Calculus, physics, and fluids/structures sequences require strong preparation.",
            },
            {
                "label": "Competitive lab access",
                "sentiment": "mixed",
                "detail": "Popular research groups admit undergraduates selectively.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech Aerospace \u2014 Undergraduate",
                "url": "https://www.ae.gatech.edu/academics/undergraduate",
            },
            {
                "label": "U.S. News \u2014 Aerospace Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/aerospace-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-aerospace-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Aerospace Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Aerospace Engineering",
                "url": "https://www.ae.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-aerospace-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Aerospace Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Aerospace Engineering",
                "url": "https://www.ae.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-analytics-ms": {
        "summary": "Students describe Scheller's on-campus M.S. in Analytics as a STEM-designated, interdisciplinary data-science degree spanning computing, engineering, and business. Reviewers praise Tech Square location, consulting and tech analytics placement, and three specialization tracks, while noting an intensive one-year pace and competitive admission relative to dedicated online analytics degrees like OMS Analytics.",
        "themes": [
            {
                "label": "Interdisciplinary analytics",
                "sentiment": "positive",
                "detail": "Joint offering across Computing, Engineering, and Scheller spans ML, optimization, and business.",
            },
            {
                "label": "Tech Square recruiting",
                "sentiment": "positive",
                "detail": "Atlanta consulting, finance, and technology firms recruit analytics graduates.",
            },
            {
                "label": "STEM designation",
                "sentiment": "positive",
                "detail": "STEM status supports OPT extensions for eligible international graduates.",
            },
            {
                "label": "Intensive pace",
                "sentiment": "caution",
                "detail": "The residential program moves quickly with team projects and practica.",
            },
            {
                "label": "Selective admission",
                "sentiment": "mixed",
                "detail": "Admission favors strong quantitative and programming preparation.",
            },
        ],
        "sources": [
            {
                "label": "Scheller \u2014 M.S. in Analytics",
                "url": "https://www.scheller.gatech.edu/degree-programs/ms-analytics/",
            },
            {
                "label": "Poets&Quants \u2014 Scheller College of Business",
                "url": "https://poetsandquants.com/school-profile/georgia-institute-of-technologys-scheller-college-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-applied-systems-engineering-pmase": {
        "summary": "Working professionals describe Georgia Tech's Professional Master's in Applied Systems Engineering as a flexible hybrid/executive graduate program; praise includes Georgia Tech faculty and employer recognition, with cautions about self-directed study and reduced campus networking versus residential programs.",
        "themes": [
            {
                "label": "Flexible delivery",
                "sentiment": "positive",
                "detail": "Online or hybrid formats suit working professionals.",
            },
            {
                "label": "Georgia Tech credential",
                "sentiment": "positive",
                "detail": "Employers recognize the Institute's engineering and computing reputation.",
            },
            {
                "label": "Professional focus",
                "sentiment": "positive",
                "detail": "Curriculum emphasizes applied skills for industry roles.",
            },
            {
                "label": "Self-directed study",
                "sentiment": "caution",
                "detail": "Online and executive formats require strong time management.",
            },
            {
                "label": "Networking trade-off",
                "sentiment": "mixed",
                "detail": "Less spontaneous campus networking than full-time residential programs.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Applied Systems Engineering",
                "url": "https://pe.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-architecture-ms": {
        "summary": "Students describe Georgia Tech's Master of Science in Architecture in the College of Design as a design-focused degree integrating technology and the built environment; praise includes studio-based learning and Atlanta urban context, with cautions about portfolio or studio workload and selective admission.",
        "themes": [
            {
                "label": "Design + technology",
                "sentiment": "positive",
                "detail": "Programs connect architecture, planning, and digital design methods.",
            },
            {
                "label": "Studio learning",
                "sentiment": "positive",
                "detail": "Design studios and practica emphasize iterative project work.",
            },
            {
                "label": "Atlanta context",
                "sentiment": "positive",
                "detail": "Urban labs and regional projects enrich coursework.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Studio and project courses require sustained hours.",
            },
            {
                "label": "Selective admission",
                "sentiment": "mixed",
                "detail": "Portfolio or statement requirements vary by program.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Architecture",
                "url": "https://arch.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/architecture",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-architecture-phd": {
        "summary": "Students describe Georgia Tech's Doctor of Philosophy in Architecture in the College of Design as a design-focused degree integrating technology and the built environment; praise includes studio-based learning and Atlanta urban context, with cautions about portfolio or studio workload and selective admission.",
        "themes": [
            {
                "label": "Design + technology",
                "sentiment": "positive",
                "detail": "Programs connect architecture, planning, and digital design methods.",
            },
            {
                "label": "Studio learning",
                "sentiment": "positive",
                "detail": "Design studios and practica emphasize iterative project work.",
            },
            {
                "label": "Atlanta context",
                "sentiment": "positive",
                "detail": "Urban labs and regional projects enrich coursework.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Studio and project courses require sustained hours.",
            },
            {
                "label": "Selective admission",
                "sentiment": "mixed",
                "detail": "Portfolio or statement requirements vary by program.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Architecture",
                "url": "https://arch.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/architecture",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-bioengineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Bioengineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Bioengineering",
                "url": "https://bme.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-bioengineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Bioengineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Bioengineering",
                "url": "https://bme.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-biomedical-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Biomedical Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Biomedical Engineering",
                "url": "https://bme.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-biomedical-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Biomedical Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Biomedical Engineering",
                "url": "https://bme.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-biomedical-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Biomedical Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Biomedical Engineering",
                "url": "https://bme.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-business-administration-bs": {
        "summary": "Students describe Scheller's B.S. in Business Administration as an undergraduate business degree at a technology-focused public university. Reviewers praise Tech Square internships, analytics and IT management threads, and strong co-op access, while noting that Scheller's undergraduate business rank trails dedicated business schools and core classes can be large.",
        "themes": [
            {
                "label": "Business + technology",
                "sentiment": "positive",
                "detail": "Curriculum connects finance, analytics, and information technology management.",
            },
            {
                "label": "Tech Square internships",
                "sentiment": "positive",
                "detail": "Atlanta tech, consulting, and finance firms recruit Scheller undergraduates.",
            },
            {
                "label": "Co-op program",
                "sentiment": "positive",
                "detail": "Georgia Tech's co-op program supports paid work experience.",
            },
            {
                "label": "Undergraduate business rank",
                "sentiment": "mixed",
                "detail": "Scheller's undergraduate rank trails top private business schools.",
            },
            {
                "label": "Program scale",
                "sentiment": "caution",
                "detail": "Gateway business courses can be large; reviewers advise early career engagement.",
            },
        ],
        "sources": [
            {
                "label": "Scheller \u2014 Undergraduate Business",
                "url": "https://www.scheller.gatech.edu/degree-programs/undergraduate/",
            },
            {
                "label": "U.S. News \u2014 Scheller Business",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/georgia-institute-of-technology-01044",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-chemical-biomolecular-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Chemical and Biomolecular Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Chemical and Biomolecular Engineering",
                "url": "https://www.chbe.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-chemical-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Chemical Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Chemical Engineering",
                "url": "https://coe.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-chemical-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Chemical Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Chemical Engineering",
                "url": "https://coe.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-civil-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Civil Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Civil Engineering",
                "url": "https://www.ce.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-civil-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Civil Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Civil Engineering",
                "url": "https://www.ce.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-civil-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Civil Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Civil Engineering",
                "url": "https://www.ce.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computational-science-engineering-ms": {
        "summary": "Students and guides describe Georgia Tech's graduate program in Computational Science and Engineering within College of Computing as a professionally focused degree at a top-35 public R1 university (U.S. News #32 nationally, 2026); praise includes Georgia Tech's faculty and Atlanta tech ecosystem, with cautions about competitive admission and program workload.",
        "themes": [
            {
                "label": "Top public research university",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech #32 nationally (#9 public, 2026).",
            },
            {
                "label": "Faculty and labs",
                "sentiment": "positive",
                "detail": "Programs in Computational Science and Engineering connect to Institute research resources.",
            },
            {
                "label": "Atlanta ecosystem",
                "sentiment": "positive",
                "detail": "Tech Square and regional employers support internships and placement.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Popular programs admit a selective share of applicants.",
            },
            {
                "label": "Program intensity",
                "sentiment": "mixed",
                "detail": "Georgia Tech's rigor is widely noted across majors.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Computational Science and Engineering",
                "url": "https://cse.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computational-science-engineering-phd": {
        "summary": "Students and guides describe Georgia Tech's doctoral program in Computational Science and Engineering within College of Computing as a research-oriented degree at a top-35 public R1 university (U.S. News #32 nationally, 2026); praise includes Georgia Tech's faculty and Atlanta tech ecosystem, with cautions about competitive admission and program workload.",
        "themes": [
            {
                "label": "Top public research university",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech #32 nationally (#9 public, 2026).",
            },
            {
                "label": "Faculty and labs",
                "sentiment": "positive",
                "detail": "Programs in Computational Science and Engineering connect to Institute research resources.",
            },
            {
                "label": "Atlanta ecosystem",
                "sentiment": "positive",
                "detail": "Tech Square and regional employers support internships and placement.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Popular programs admit a selective share of applicants.",
            },
            {
                "label": "Program intensity",
                "sentiment": "mixed",
                "detail": "Georgia Tech's rigor is widely noted across majors.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Computational Science and Engineering",
                "url": "https://cse.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computer-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Computer Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Computer Engineering",
                "url": "https://www.ece.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computer-science-ms": {
        "summary": "Graduate applicants describe Georgia Tech's on-campus M.S. in Computer Science as a top-ranked research and coursework degree within a perennial top-10 CS department; praise includes funded research assistantships, IRIM and IDEaS institute access, and strong Atlanta tech recruiting, with cautions about competitive admission and self-funded tuition for terminal master's students without assistantships.",
        "themes": [
            {
                "label": "Top-10 CS reputation",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech CS among the nation's best graduate programs.",
            },
            {
                "label": "Research institutes",
                "sentiment": "positive",
                "detail": "IRIM, IDEaS, and the School of Cybersecurity and Privacy anchor AI, robotics, and security research.",
            },
            {
                "label": "Atlanta tech recruiting",
                "sentiment": "positive",
                "detail": "Graduates recruit into major technology firms and Atlanta's growing tech sector.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Strong quantitative and computing backgrounds are expected for competitive applicants.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech College of Computing \u2014 Graduate",
                "url": "https://www.cc.gatech.edu/graduate",
            },
            {
                "label": "U.S. News \u2014 Computer Science Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-computer-science-phd": {
        "summary": "Graduate applicants describe Georgia Tech's Doctor of Philosophy in Computer Science as a degree within a top-ranked College of Computing; praise includes AI, systems, and security research and Atlanta tech recruiting, with cautions about competitive admission and demanding doctoral research expectations.",
        "themes": [
            {
                "label": "Top CS reputation",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech CS among the nation's best programs.",
            },
            {
                "label": "Research depth",
                "sentiment": "positive",
                "detail": "Faculty lead research in AI, systems, robotics, and cybersecurity.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Graduates recruit into major technology firms and Atlanta employers.",
            },
            {
                "label": "Selective admission",
                "sentiment": "caution",
                "detail": "Strong computing and quantitative backgrounds are expected.",
            },
            {
                "label": "Program intensity",
                "sentiment": "mixed",
                "detail": "Coursework and research expectations are rigorous at scale.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Computer Science",
                "url": "https://www.cc.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-economics-bs": {
        "summary": "Students describe Georgia Tech's Bachelor of Science in Economics in the School of Economics as a quantitatively oriented program at a technology-focused public university; praise includes econometrics training and policy interfaces, with cautions that introductory courses can be large and career paths vary without further graduate study.",
        "themes": [
            {
                "label": "Quantitative economics",
                "sentiment": "positive",
                "detail": "Coursework emphasizes econometrics, data analysis, and policy applications.",
            },
            {
                "label": "Tech-university context",
                "sentiment": "positive",
                "detail": "Interdisciplinary ties to computing, engineering, and public policy.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition supports affordability for Georgia residents.",
            },
            {
                "label": "Large intro sections",
                "sentiment": "caution",
                "detail": "Gateway courses can be large; reviewers advise office hours and recitation.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes split between graduate study, consulting, analytics, and policy.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Economics",
                "url": "https://econ.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-economics-international-affairs-bs": {
        "summary": "Students describe Georgia Tech's Bachelor of Science in Economics and International Affairs in the School of Economics as a quantitatively oriented program at a technology-focused public university; praise includes econometrics training and policy interfaces, with cautions that introductory courses can be large and career paths vary without further graduate study.",
        "themes": [
            {
                "label": "Quantitative economics",
                "sentiment": "positive",
                "detail": "Coursework emphasizes econometrics, data analysis, and policy applications.",
            },
            {
                "label": "Tech-university context",
                "sentiment": "positive",
                "detail": "Interdisciplinary ties to computing, engineering, and public policy.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition supports affordability for Georgia residents.",
            },
            {
                "label": "Large intro sections",
                "sentiment": "caution",
                "detail": "Gateway courses can be large; reviewers advise office hours and recitation.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes split between graduate study, consulting, analytics, and policy.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Economics and International Affairs",
                "url": "https://iac.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-economics-ms": {
        "summary": "Students describe Georgia Tech's Master of Science in Economics in the School of Economics as a quantitatively oriented program at a technology-focused public university; praise includes econometrics training and policy interfaces, with cautions that introductory courses can be large and career paths vary without further graduate study.",
        "themes": [
            {
                "label": "Quantitative economics",
                "sentiment": "positive",
                "detail": "Coursework emphasizes econometrics, data analysis, and policy applications.",
            },
            {
                "label": "Tech-university context",
                "sentiment": "positive",
                "detail": "Interdisciplinary ties to computing, engineering, and public policy.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition supports affordability for Georgia residents.",
            },
            {
                "label": "Large intro sections",
                "sentiment": "caution",
                "detail": "Gateway courses can be large; reviewers advise office hours and recitation.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes split between graduate study, consulting, analytics, and policy.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Economics",
                "url": "https://econ.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-economics-phd": {
        "summary": "Students describe Georgia Tech's Doctor of Philosophy in Economics in the School of Economics as a quantitatively oriented program at a technology-focused public university; praise includes econometrics training and policy interfaces, with cautions that introductory courses can be large and career paths vary without further graduate study.",
        "themes": [
            {
                "label": "Quantitative economics",
                "sentiment": "positive",
                "detail": "Coursework emphasizes econometrics, data analysis, and policy applications.",
            },
            {
                "label": "Tech-university context",
                "sentiment": "positive",
                "detail": "Interdisciplinary ties to computing, engineering, and public policy.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition supports affordability for Georgia residents.",
            },
            {
                "label": "Large intro sections",
                "sentiment": "caution",
                "detail": "Gateway courses can be large; reviewers advise office hours and recitation.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes split between graduate study, consulting, analytics, and policy.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Economics",
                "url": "https://econ.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-electrical-computer-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Electrical and Computer Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Electrical and Computer Engineering",
                "url": "https://www.ece.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-electrical-computer-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Electrical and Computer Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Electrical and Computer Engineering",
                "url": "https://www.ece.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-electrical-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Electrical Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Electrical Engineering",
                "url": "https://coe.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-engineering-science-mechanics-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Engineering Science and Mechanics as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Engineering Science and Mechanics",
                "url": "https://www.me.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-engineering-science-mechanics-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Engineering Science and Mechanics as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Engineering Science and Mechanics",
                "url": "https://www.me.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-environmental-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Environmental Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Environmental Engineering",
                "url": "https://www.ce.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-environmental-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Environmental Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Environmental Engineering",
                "url": "https://www.ce.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-environmental-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Environmental Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Environmental Engineering",
                "url": "https://www.ce.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-global-economics-modern-languages-bs": {
        "summary": "Students describe Georgia Tech's Bachelor of Science in Global Economics and Modern Languages in the School of Economics as a quantitatively oriented program at a technology-focused public university; praise includes econometrics training and policy interfaces, with cautions that introductory courses can be large and career paths vary without further graduate study.",
        "themes": [
            {
                "label": "Quantitative economics",
                "sentiment": "positive",
                "detail": "Coursework emphasizes econometrics, data analysis, and policy applications.",
            },
            {
                "label": "Tech-university context",
                "sentiment": "positive",
                "detail": "Interdisciplinary ties to computing, engineering, and public policy.",
            },
            {
                "label": "Public-university value",
                "sentiment": "positive",
                "detail": "In-state tuition supports affordability for Georgia residents.",
            },
            {
                "label": "Large intro sections",
                "sentiment": "caution",
                "detail": "Gateway courses can be large; reviewers advise office hours and recitation.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes split between graduate study, consulting, analytics, and policy.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Global Economics and Modern Languages",
                "url": "https://iac.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-industrial-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Industrial Engineering in the H. Milton Stewart School of ISyE as the nation's top-ranked undergraduate IE program (U.S. News #1). Reviewers praise the quantitative analytics curriculum, the century-old co-op program, and placement into consulting, supply chain, and tech analytics roles, while noting demanding coursework and large class sizes in core sequences.",
        "themes": [
            {
                "label": "#1 industrial engineering",
                "sentiment": "positive",
                "detail": "U.S. News consistently ranks Georgia Tech ISyE #1 nationally at both undergraduate and graduate levels.",
            },
            {
                "label": "Analytics & operations focus",
                "sentiment": "positive",
                "detail": "Curriculum spans optimization, statistics, and data-driven decision making.",
            },
            {
                "label": "Co-op and placement",
                "sentiment": "positive",
                "detail": "Georgia Tech's co-op program and Atlanta employers support strong internship and job outcomes.",
            },
            {
                "label": "Rigorous quantitative core",
                "sentiment": "caution",
                "detail": "Probability, optimization, and statistics sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "ISyE is one of Georgia Tech's largest majors; core courses can be large.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech ISyE \u2014 Undergraduate",
                "url": "https://www.isye.gatech.edu/academics/undergraduate",
            },
            {
                "label": "U.S. News \u2014 Industrial Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-industrial-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Industrial Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Industrial Engineering",
                "url": "https://www.isye.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-industrial-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Industrial Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Industrial Engineering",
                "url": "https://www.isye.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-march": {
        "summary": "Students describe Georgia Tech's Master of Architecture (M.Arch) as a NAAB-accredited professional degree with design studios, building technology, and history/theory. Reviewers praise the College of Design's technology focus and Atlanta urban-design context, while noting demanding studio workloads and portfolio-driven admission.",
        "themes": [
            {
                "label": "NAAB-accredited professional degree",
                "sentiment": "positive",
                "detail": "The M.Arch satisfies licensure pathways toward the Architect Registration Examination.",
            },
            {
                "label": "Design + technology",
                "sentiment": "positive",
                "detail": "Studios integrate digital fabrication, sustainability, and building science.",
            },
            {
                "label": "Atlanta urban context",
                "sentiment": "positive",
                "detail": "City-regional planning and real-estate programs enrich urban design coursework.",
            },
            {
                "label": "Studio workload",
                "sentiment": "caution",
                "detail": "Design studios require long hours and iterative critique cycles.",
            },
            {
                "label": "Portfolio admission",
                "sentiment": "mixed",
                "detail": "Admission is selective and portfolio-driven.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech School of Architecture \u2014 M.Arch",
                "url": "https://arch.gatech.edu/",
            },
            {
                "label": "U.S. News \u2014 Architecture Programs",
                "url": "https://www.usnews.com/best-colleges/rankings/architecture",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-materials-science-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Materials Science and Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Materials Science and Engineering",
                "url": "https://www.mse.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-materials-science-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Materials Science and Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Materials Science and Engineering",
                "url": "https://www.mse.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-materials-science-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Materials Science and Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Materials Science and Engineering",
                "url": "https://www.mse.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mba-global-business-executive": {
        "summary": "Working executives describe Scheller's Executive MBA in Global Business as a part-time MBA with international residencies and Tech Square immersion. Reviewers praise the business-meets-technology positioning and Jones MBA Career Center support, while noting travel demands for global modules and a smaller national brand than top-10 executive MBA programs.",
        "themes": [
            {
                "label": "Global executive format",
                "sentiment": "positive",
                "detail": "International residencies and a part-time schedule suit traveling executives.",
            },
            {
                "label": "Tech Square location",
                "sentiment": "positive",
                "detail": "Immersion in Atlanta's technology and innovation district.",
            },
            {
                "label": "Career services",
                "sentiment": "positive",
                "detail": "Jones MBA Career Center supports executive career transitions.",
            },
            {
                "label": "Travel requirements",
                "sentiment": "caution",
                "detail": "Global modules require time away from work and family.",
            },
            {
                "label": "Regional brand",
                "sentiment": "mixed",
                "detail": "Strong in the Southeast; less national reach than M7 executive programs.",
            },
        ],
        "sources": [
            {
                "label": "Scheller \u2014 Executive MBA Global Business",
                "url": "https://www.scheller.gatech.edu/degree-programs/executive-mba-global-business/",
            },
            {
                "label": "Poets&Quants \u2014 Scheller College of Business",
                "url": "https://poetsandquants.com/school-profile/georgia-institute-of-technologys-scheller-college-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mba-management-technology-executive": {
        "summary": "Technology leaders describe Scheller's Executive MBA in Management of Technology as a part-time program for managers bridging engineering and business strategy. Reviewers praise Tech Square access and a cohort of experienced technologists, while noting weekend residency demands and outcomes concentrated in tech management rather than traditional consulting or finance.",
        "themes": [
            {
                "label": "Technology management focus",
                "sentiment": "positive",
                "detail": "Curriculum connects product, operations, and strategy for tech leaders.",
            },
            {
                "label": "Experienced cohort",
                "sentiment": "positive",
                "detail": "Peers bring engineering and product-management backgrounds.",
            },
            {
                "label": "Tech Square ecosystem",
                "sentiment": "positive",
                "detail": "Atlanta tech firms and startups surround the Scheller campus.",
            },
            {
                "label": "Weekend residencies",
                "sentiment": "caution",
                "detail": "Monthly on-campus sessions require sustained time commitment.",
            },
            {
                "label": "Narrower recruiting",
                "sentiment": "mixed",
                "detail": "Best suited for tech leadership paths rather than investment banking.",
            },
        ],
        "sources": [
            {
                "label": "Scheller \u2014 Executive MBA Management of Technology",
                "url": "https://www.scheller.gatech.edu/degree-programs/executive-mba-management-of-technology/",
            },
            {
                "label": "Poets&Quants \u2014 Scheller College of Business",
                "url": "https://poetsandquants.com/school-profile/georgia-institute-of-technologys-scheller-college-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mechanical-engineering-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Mechanical Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Mechanical Engineering",
                "url": "https://www.me.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mechanical-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Mechanical Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Mechanical Engineering",
                "url": "https://www.me.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mechanical-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Mechanical Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Mechanical Engineering",
                "url": "https://www.me.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-mechanical-engineering-undesignated-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Mechanical Engineering (Undesignated) as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Mechanical Engineering",
                "url": "https://www.me.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-nuclear-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Nuclear Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Nuclear Engineering",
                "url": "https://www.nre.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-nuclear-engineering-phd": {
        "summary": "Doctoral students describe Georgia Tech's Ph.D. in Nuclear Engineering as a research degree within a top public R1 engineering college; praise includes funded assistantships in many groups, GTRI and interdisciplinary institute access, and strong industry and national lab placement, with cautions about competitive funding and academic job-market variability.",
        "themes": [
            {
                "label": "R1 engineering research",
                "sentiment": "positive",
                "detail": "Doctoral students work with faculty across a top public research university.",
            },
            {
                "label": "GTRI and labs",
                "sentiment": "positive",
                "detail": "Major research centers and GTRI support applied engineering scholarship.",
            },
            {
                "label": "Interdisciplinary access",
                "sentiment": "positive",
                "detail": "Institutes span robotics, energy, manufacturing, and bioengineering.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Fellowships and assistantships are competitive across departments.",
            },
            {
                "label": "Academic market",
                "sentiment": "caution",
                "detail": "Tenure-track faculty hiring varies by field nationally.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Nuclear Engineering",
                "url": "https://www.nre.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-nuclear-radiological-bs": {
        "summary": "Students describe Georgia Tech's B.S. in Nuclear and Radiological Engineering as a rigorous engineering degree within one of the nation's largest and top-ranked engineering colleges; praise includes the co-op program, GTRI research access, and strong industry placement, with cautions about demanding math and physics prerequisites and large core classes.",
        "themes": [
            {
                "label": "Top engineering college",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech Engineering among the nation's best.",
            },
            {
                "label": "Co-op and internships",
                "sentiment": "positive",
                "detail": "Georgia Tech's century-old co-op program supports paid work experience.",
            },
            {
                "label": "Industry placement",
                "sentiment": "positive",
                "detail": "Graduates recruit into aerospace, tech, consulting, and manufacturing employers.",
            },
            {
                "label": "Rigorous core",
                "sentiment": "caution",
                "detail": "Calculus, physics, and major sequences are mathematically demanding.",
            },
            {
                "label": "Large program scale",
                "sentiment": "mixed",
                "detail": "Popular engineering majors can mean large introductory sections.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Nuclear and Radiological Engineering",
                "url": "https://www.nre.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-ocean-science-engineering-phd": {
        "summary": "Students and guides describe Georgia Tech's doctoral program in Ocean Science and Engineering within College of Sciences as a research-oriented degree at a top-35 public R1 university (U.S. News #32 nationally, 2026); praise includes Georgia Tech's faculty and Atlanta tech ecosystem, with cautions about competitive admission and program workload.",
        "themes": [
            {
                "label": "Top public research university",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech #32 nationally (#9 public, 2026).",
            },
            {
                "label": "Faculty and labs",
                "sentiment": "positive",
                "detail": "Programs in Ocean Science and Engineering connect to Institute research resources.",
            },
            {
                "label": "Atlanta ecosystem",
                "sentiment": "positive",
                "detail": "Tech Square and regional employers support internships and placement.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Popular programs admit a selective share of applicants.",
            },
            {
                "label": "Program intensity",
                "sentiment": "mixed",
                "detail": "Georgia Tech's rigor is widely noted across majors.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Ocean Science and Engineering",
                "url": "https://cos.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.gatech.edu/about/rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-quantitative-computational-finance-ms": {
        "summary": "Students describe Scheller's M.S. in Quantitative and Computational Finance (QCF) as a STEM-designated program blending financial engineering, computing, and operations research. Reviewers praise placement into trading, risk, and fintech roles and the Tech Square ecosystem, while noting mathematically demanding coursework and a smaller cohort than general MBA or analytics programs.",
        "themes": [
            {
                "label": "Quant finance rigor",
                "sentiment": "positive",
                "detail": "Curriculum spans stochastic calculus, optimization, and computational finance.",
            },
            {
                "label": "STEM & placement",
                "sentiment": "positive",
                "detail": "Graduates enter quantitative trading, risk, consulting, and fintech roles.",
            },
            {
                "label": "Tech Square ecosystem",
                "sentiment": "positive",
                "detail": "Atlanta finance and technology employers recruit QCF graduates.",
            },
            {
                "label": "Mathematical demands",
                "sentiment": "caution",
                "detail": "Strong probability, linear algebra, and programming are prerequisites.",
            },
            {
                "label": "Small specialized cohort",
                "sentiment": "mixed",
                "detail": "A niche program with fewer seats than general business master's tracks.",
            },
        ],
        "sources": [
            {
                "label": "Scheller \u2014 M.S. in Quantitative and Computational Finance",
                "url": "https://www.scheller.gatech.edu/degree-programs/ms-quantitative-computational-finance/",
            },
            {
                "label": "Poets&Quants \u2014 Scheller College of Business",
                "url": "https://poetsandquants.com/school-profile/georgia-institute-of-technologys-scheller-college-of-business/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-supply-chain-engineering-ms": {
        "summary": "Graduate students describe Georgia Tech's Master of Science in Supply Chain Engineering as a research and coursework degree within the College of Engineering; praise includes top-ranked faculty labs, GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive funding for terminal master's students and demanding technical prerequisites.",
        "themes": [
            {
                "label": "Top engineering reputation",
                "sentiment": "positive",
                "detail": "Georgia Tech Engineering is consistently ranked among U.S. leaders.",
            },
            {
                "label": "Research and GTRI access",
                "sentiment": "positive",
                "detail": "Graduate students work in major labs and Georgia Tech Research Institute projects.",
            },
            {
                "label": "Industry recruiting",
                "sentiment": "positive",
                "detail": "Atlanta and national employers recruit engineering graduates.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive; terminal MS students may self-fund.",
            },
            {
                "label": "Technical prerequisites",
                "sentiment": "caution",
                "detail": "Graduate sequences assume strong math and engineering foundations.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Supply Chain Engineering",
                "url": "https://www.isye.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-urban-analytics-ms": {
        "summary": "Students describe Georgia Tech's Master of Science in Urban Analytics in the College of Design as a design-focused degree integrating technology and the built environment; praise includes studio-based learning and Atlanta urban context, with cautions about portfolio or studio workload and selective admission.",
        "themes": [
            {
                "label": "Design + technology",
                "sentiment": "positive",
                "detail": "Programs connect architecture, planning, and digital design methods.",
            },
            {
                "label": "Studio learning",
                "sentiment": "positive",
                "detail": "Design studios and practica emphasize iterative project work.",
            },
            {
                "label": "Atlanta context",
                "sentiment": "positive",
                "detail": "Urban labs and regional projects enrich coursework.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Studio and project courses require sustained hours.",
            },
            {
                "label": "Selective admission",
                "sentiment": "mixed",
                "detail": "Portfolio or statement requirements vary by program.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Urban Analytics",
                "url": "https://planning.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/architecture",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "gatech-urban-planning-and-spatial-analytics-bs": {
        "summary": "Students describe Georgia Tech's Bachelor of Science in Urban Planning and Spatial Analytics in the College of Design as a design-focused degree integrating technology and the built environment; praise includes studio-based learning and Atlanta urban context, with cautions about portfolio or studio workload and selective admission.",
        "themes": [
            {
                "label": "Design + technology",
                "sentiment": "positive",
                "detail": "Programs connect architecture, planning, and digital design methods.",
            },
            {
                "label": "Studio learning",
                "sentiment": "positive",
                "detail": "Design studios and practica emphasize iterative project work.",
            },
            {
                "label": "Atlanta context",
                "sentiment": "positive",
                "detail": "Urban labs and regional projects enrich coursework.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Studio and project courses require sustained hours.",
            },
            {
                "label": "Selective admission",
                "sentiment": "mixed",
                "detail": "Portfolio or statement requirements vary by program.",
            },
        ],
        "sources": [
            {
                "label": "Georgia Tech \u2014 Urban Planning and Spatial Analytics",
                "url": "https://planning.gatech.edu/",
            },
            {
                "label": "Georgia Tech \u2014 Rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/architecture",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
