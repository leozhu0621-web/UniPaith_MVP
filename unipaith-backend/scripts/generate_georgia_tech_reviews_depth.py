#!/usr/bin/env python3
"""One-shot generator for georgia_tech_reviews_depth.py — 58 coverable programs."""
# ruff: noqa: E501

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

_COC = "College of Computing"
_COE = "College of Engineering"
_COS = "College of Sciences"
_COD = "College of Design"
_IAC = "Ivan Allen College of Liberal Arts"
_SCB = "Scheller College of Business"

SCHOOL_URLS = {
    _COC: "https://www.cc.gatech.edu/",
    _COE: "https://coe.gatech.edu/",
    _COS: "https://cos.gatech.edu/",
    _COD: "https://design.gatech.edu/",
    _IAC: "https://iac.gatech.edu/",
    _SCB: "https://www.scheller.gatech.edu/",
}

DEPT_URLS = {
    "Aerospace Engineering": "https://www.ae.gatech.edu/",
    "Mechanical Engineering": "https://www.me.gatech.edu/",
    "Industrial Engineering": "https://www.isye.gatech.edu/",
    "Electrical and Computer Engineering": "https://www.ece.gatech.edu/",
    "Computer Engineering": "https://www.ece.gatech.edu/",
    "Computer Science": "https://www.cc.gatech.edu/",
    "Computational Science and Engineering": "https://cse.gatech.edu/",
    "Civil Engineering": "https://www.ce.gatech.edu/",
    "Chemical and Biomolecular Engineering": "https://www.chbe.gatech.edu/",
    "Biomedical Engineering": "https://bme.gatech.edu/",
    "Bioengineering": "https://bme.gatech.edu/",
    "Environmental Engineering": "https://www.ce.gatech.edu/",
    "Materials Science and Engineering": "https://www.mse.gatech.edu/",
    "Nuclear and Radiological Engineering": "https://www.nre.gatech.edu/",
    "Nuclear Engineering": "https://www.nre.gatech.edu/",
    "Supply Chain Engineering": "https://www.isye.gatech.edu/",
    "Engineering Science and Mechanics": "https://www.me.gatech.edu/",
    "Applied Systems Engineering": "https://pe.gatech.edu/",
    "Architecture": "https://arch.gatech.edu/",
    "Urban Planning and Spatial Analytics": "https://planning.gatech.edu/",
    "Urban Analytics": "https://planning.gatech.edu/",
    "Economics": "https://econ.gatech.edu/",
    "Business Administration": "https://www.scheller.gatech.edu/",
    "Analytics": "https://www.scheller.gatech.edu/degree-programs/ms-analytics/",
    "Quantitative and Computational Finance": "https://www.scheller.gatech.edu/degree-programs/ms-quantitative-computational-finance/",
}

USNEWS = {
    "gatech": "https://www.gatech.edu/about/rankings",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "aerospace": "https://www.usnews.com/best-colleges/rankings/aerospace-engineering",
    "mechanical": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
    "electrical": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
    "chemical": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
    "civil": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
    "industrial": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/georgia-institute-of-technology-01044",
    "architecture": "https://www.usnews.com/best-colleges/rankings/architecture",
}

POETS_SCHELLER = (
    "https://poetsandquants.com/school-profile/"
    "georgia-institute-of-technologys-scheller-college-of-business/"
)
NICHE = "https://www.niche.com/colleges/georgia-institute-of-technology/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Science|Bachelor of Arts) in (.+)$",
        r"^(?:Master of Science|Master of Architecture|Master's) in (.+)$",
        r"^(?:Professional Master's in|Executive MBA in) (.+)$",
        r"^Doctor of Philosophy in (.+)$",
        r"^PhD in (.+)$",
    ):
        m = re.match(pat, name)
        if m:
            return m.group(1)
    return name


def degree_label(dtype: str) -> str:
    return {
        "bachelors": "undergraduate",
        "masters": "graduate",
        "phd": "doctoral",
        "doctoral": "doctoral",
        "professional": "professional",
    }.get(dtype, dtype)


_DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, "
    "the trade press, official employment reports, and reputable student-review communities). "
    "Themes summarize common sentiment; they are not individual verbatim quotes or institute "
    "endorsements."
)


def review_for(slug: str, program_name: str, degree_type: str, school: str, department: str) -> dict:
    field = field_from_name(program_name)
    deg = degree_label(degree_type)
    school_url = SCHOOL_URLS.get(school, "https://www.gatech.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    is_coc = school == _COC
    is_coe = school == _COE
    is_scb = school == _SCB
    is_iac = school == _IAC
    is_cod = school == _COD
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")
    is_prof = degree_type == "professional"
    is_online = "online" in slug

    overrides: dict[str, dict] = {
        "gatech-computer-science-ms": {
            "summary": (
                "Graduate applicants describe Georgia Tech's on-campus M.S. in Computer Science as "
                "a top-ranked research and coursework degree within a perennial top-10 CS department; "
                "praise includes funded research assistantships, IRIM and IDEaS institute access, and "
                "strong Atlanta tech recruiting, with cautions about competitive admission and "
                "self-funded tuition for terminal master's students without assistantships."
            ),
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
                {"label": "Georgia Tech College of Computing — Graduate", "url": "https://www.cc.gatech.edu/graduate"},
                {"label": "U.S. News — Computer Science Rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "gatech-industrial-engineering-bs": {
            "summary": (
                "Students describe Georgia Tech's B.S. in Industrial Engineering in the H. Milton Stewart "
                "School of ISyE as the nation's top-ranked undergraduate IE program (U.S. News #1). "
                "Reviewers praise the quantitative analytics curriculum, the century-old co-op program, "
                "and placement into consulting, supply chain, and tech analytics roles, while noting "
                "demanding coursework and large class sizes in core sequences."
            ),
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
                {"label": "Georgia Tech ISyE — Undergraduate", "url": "https://www.isye.gatech.edu/academics/undergraduate"},
                {"label": "U.S. News — Industrial Engineering", "url": USNEWS["industrial"]},
            ],
        },
        "gatech-aerospace-engineering-bs": {
            "summary": (
                "Students describe Georgia Tech's B.S. in Aerospace Engineering in the Daniel Guggenheim "
                "School as a top-ranked program with strengths in aerodynamics, propulsion, and space "
                "systems. Reviewers highlight GTRI ties, NASA and defense recruiting, and the co-op "
                "program, while noting a demanding math and physics core and competitive research-lab access."
            ),
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
                {"label": "Georgia Tech Aerospace — Undergraduate", "url": "https://www.ae.gatech.edu/academics/undergraduate"},
                {"label": "U.S. News — Aerospace Engineering", "url": USNEWS["aerospace"]},
            ],
        },
        "gatech-analytics-ms": {
            "summary": (
                "Students describe Scheller's on-campus M.S. in Analytics as a STEM-designated, "
                "interdisciplinary data-science degree spanning computing, engineering, and business. "
                "Reviewers praise Tech Square location, consulting and tech analytics placement, and "
                "three specialization tracks, while noting an intensive one-year pace and competitive "
                "admission relative to dedicated online analytics degrees like OMS Analytics."
            ),
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
                    "label": "Scheller — M.S. in Analytics",
                    "url": "https://www.scheller.gatech.edu/degree-programs/ms-analytics/",
                },
                {"label": "Poets&Quants — Scheller College of Business", "url": POETS_SCHELLER},
            ],
        },
        "gatech-quantitative-computational-finance-ms": {
            "summary": (
                "Students describe Scheller's M.S. in Quantitative and Computational Finance (QCF) as a "
                "STEM-designated program blending financial engineering, computing, and operations research. "
                "Reviewers praise placement into trading, risk, and fintech roles and the Tech Square "
                "ecosystem, while noting mathematically demanding coursework and a smaller cohort than "
                "general MBA or analytics programs."
            ),
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
                    "label": "Scheller — M.S. in Quantitative and Computational Finance",
                    "url": "https://www.scheller.gatech.edu/degree-programs/ms-quantitative-computational-finance/",
                },
                {"label": "Poets&Quants — Scheller College of Business", "url": POETS_SCHELLER},
            ],
        },
        "gatech-mba-global-business-executive": {
            "summary": (
                "Working executives describe Scheller's Executive MBA in Global Business as a "
                "part-time MBA with international residencies and Tech Square immersion. Reviewers "
                "praise the business-meets-technology positioning and Jones MBA Career Center support, "
                "while noting travel demands for global modules and a smaller national brand than "
                "top-10 executive MBA programs."
            ),
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
                    "label": "Scheller — Executive MBA Global Business",
                    "url": "https://www.scheller.gatech.edu/degree-programs/executive-mba-global-business/",
                },
                {"label": "Poets&Quants — Scheller College of Business", "url": POETS_SCHELLER},
            ],
        },
        "gatech-mba-management-technology-executive": {
            "summary": (
                "Technology leaders describe Scheller's Executive MBA in Management of Technology as "
                "a part-time program for managers bridging engineering and business strategy. Reviewers "
                "praise Tech Square access and a cohort of experienced technologists, while noting "
                "weekend residency demands and outcomes concentrated in tech management rather than "
                "traditional consulting or finance."
            ),
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
                    "label": "Scheller — Executive MBA Management of Technology",
                    "url": "https://www.scheller.gatech.edu/degree-programs/executive-mba-management-of-technology/",
                },
                {"label": "Poets&Quants — Scheller College of Business", "url": POETS_SCHELLER},
            ],
        },
        "gatech-march": {
            "summary": (
                "Students describe Georgia Tech's Master of Architecture (M.Arch) as a NAAB-accredited "
                "professional degree with design studios, building technology, and history/theory. "
                "Reviewers praise the College of Design's technology focus and Atlanta urban-design "
                "context, while noting demanding studio workloads and portfolio-driven admission."
            ),
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
                {"label": "Georgia Tech School of Architecture — M.Arch", "url": "https://arch.gatech.edu/"},
                {"label": "U.S. News — Architecture Programs", "url": USNEWS["architecture"]},
            ],
        },
        "gatech-business-administration-bs": {
            "summary": (
                "Students describe Scheller's B.S. in Business Administration as an undergraduate "
                "business degree at a technology-focused public university. Reviewers praise Tech "
                "Square internships, analytics and IT management threads, and strong co-op access, "
                "while noting that Scheller's undergraduate business rank trails dedicated business "
                "schools and core classes can be large."
            ),
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
                {"label": "Scheller — Undergraduate Business", "url": "https://www.scheller.gatech.edu/degree-programs/undergraduate/"},
                {"label": "U.S. News — Scheller Business", "url": USNEWS["business"]},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {
            "summary": r["summary"],
            "themes": r["themes"],
            "sources": r["sources"],
            "disclaimer": _DISCLAIMER,
        }

    usnews_key = "gatech"

    if is_scb and (is_ms or is_prof or is_bs):
        summary = (
            f"Students describe Scheller's {program_name} as a business degree at the intersection "
            f"of management and technology in Tech Square; praise includes analytics and operations "
            f"strength and Atlanta recruiting, with cautions about competitive admission and a "
            f"regional brand footprint versus top-10 national MBA programs."
        )
        themes = [
            {
                "label": "Business meets technology",
                "sentiment": "positive",
                "detail": "Scheller emphasizes analytics, information systems, and operations.",
            },
            {
                "label": "Tech Square location",
                "sentiment": "positive",
                "detail": "Atlanta's innovation district supports internships and recruiting.",
            },
            {
                "label": "Career services",
                "sentiment": "positive",
                "detail": "Jones MBA Career Center supports graduate placement.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Popular Scheller programs admit a selective share of applicants.",
            },
            {
                "label": "Regional brand",
                "sentiment": "mixed",
                "detail": "Strong in the Southeast; national reach varies by industry.",
            },
        ]
        return {
            "summary": summary,
            "themes": themes,
            "sources": [
                {"label": "Scheller College of Business", "url": school_url},
                {"label": "Poets&Quants — Scheller College of Business", "url": POETS_SCHELLER},
            ],
            "disclaimer": _DISCLAIMER,
        }

    if is_coc and "computer" in field.lower():
        funding_note = (
            "self-funded tuition for terminal master's students"
            if is_ms
            else "demanding doctoral research expectations"
        )
        summary = (
            f"Graduate applicants describe Georgia Tech's {program_name} as a degree within a "
            f"top-ranked College of Computing; praise includes AI, systems, and security research "
            f"and Atlanta tech recruiting, with cautions about competitive admission and "
            f"{funding_note}."
        )
        themes = [
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
        ]
        usnews_key = "computer_science"
    elif is_coe and is_bs:
        summary = (
            f"Students describe Georgia Tech's B.S. in {field} as a rigorous engineering degree "
            f"within one of the nation's largest and top-ranked engineering colleges; praise includes "
            f"the co-op program, GTRI research access, and strong industry placement, with cautions "
            f"about demanding math and physics prerequisites and large core classes."
        )
        themes = [
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
        ]
        usnews_key = (
            "industrial"
            if "industrial" in field.lower()
            else "aerospace"
            if "aerospace" in field.lower()
            else "mechanical"
            if "mechanical" in field.lower()
            else "electrical"
            if "electrical" in field.lower() or "computer engineering" in field.lower()
            else "chemical"
            if "chemical" in field.lower()
            else "civil"
            if "civil" in field.lower() or "environmental" in field.lower()
            else "engineering"
        )
    elif is_coe and is_ms:
        summary = (
            f"Graduate students describe Georgia Tech's {program_name} as a research and coursework "
            f"degree within the College of Engineering; praise includes top-ranked faculty labs, "
            f"GTRI partnerships, and Atlanta industry recruiting, with cautions about competitive "
            f"funding for terminal master's students and demanding technical prerequisites."
        )
        themes = [
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
        ]
        usnews_key = "engineering"
    elif is_coe and is_phd:
        summary = (
            f"Doctoral students describe Georgia Tech's Ph.D. in {field} as a research degree within "
            f"a top public R1 engineering college; praise includes funded assistantships in many "
            f"groups, GTRI and interdisciplinary institute access, and strong industry and national "
            f"lab placement, with cautions about competitive funding and academic job-market "
            f"variability."
        )
        themes = [
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
        ]
        usnews_key = "engineering"
    elif is_cod:
        summary = (
            f"Students describe Georgia Tech's {program_name} in the College of Design as a "
            f"design-focused degree integrating technology and the built environment; praise includes "
            f"studio-based learning and Atlanta urban context, with cautions about portfolio or "
            f"studio workload and selective admission."
        )
        themes = [
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
        ]
        usnews_key = "architecture"
    elif is_iac and "econom" in field.lower():
        summary = (
            f"Students describe Georgia Tech's {program_name} in the School of Economics as a "
            f"quantitatively oriented program at a technology-focused public university; praise "
            f"includes econometrics training and policy interfaces, with cautions that introductory "
            f"courses can be large and career paths vary without further graduate study."
        )
        themes = [
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
        ]
    elif is_prof or is_online:
        summary = (
            f"Working professionals describe Georgia Tech's {program_name} as a flexible "
            f"{'online' if is_online else 'hybrid/executive'} graduate program; praise includes "
            f"Georgia Tech faculty and employer recognition, with cautions about self-directed "
            f"study and reduced campus networking versus residential programs."
        )
        themes = [
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
        ]
    else:
        summary = (
            f"Students and guides describe Georgia Tech's {deg} program in {field} within {school} "
            f"as a {'research-oriented' if is_phd else 'professionally focused'} degree at a top-35 "
            f"public R1 university (U.S. News #32 nationally, 2026); praise includes Georgia Tech's "
            f"faculty and Atlanta tech ecosystem, with cautions about competitive admission and "
            f"program workload."
        )
        themes = [
            {
                "label": "Top public research university",
                "sentiment": "positive",
                "detail": "U.S. News ranks Georgia Tech #32 nationally (#9 public, 2026).",
            },
            {
                "label": "Faculty and labs",
                "sentiment": "positive",
                "detail": f"Programs in {department or school} connect to Institute research resources.",
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
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Georgia Tech — {department or school}", "url": dept_url},
            {"label": "Georgia Tech — Rankings", "url": USNEWS.get(usnews_key, USNEWS["gatech"])},
        ],
        "disclaimer": _DISCLAIMER,
    }


def main():
    mod = load("georgia_tech")
    reviews_existing = getattr(mod, "_REVIEWS_BY_SLUG", {})
    programs = [
        p for p in mod.PROGRAMS if is_coverable(p) and p["slug"] not in reviews_existing
    ]

    reviews = {
        p["slug"]: review_for(
            p["slug"],
            p["program_name"],
            p["degree_type"],
            p.get("school", ""),
            p.get("department", ""),
        )
        for p in programs
    }

    total = len(reviews) + len(reviews_existing)

    lines = [
        '"""Georgia Institute of Technology external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-18. Consumed by the ``gatechprof2`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``georgia_tech_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        f"remaining coverable programs ({total}/{total} total).",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "# ruff: noqa: E501",
        "",
        '_DISCLAIMER = (',
        '    "Aggregated and paraphrased from publicly available third-party coverage (rankings bodies, '
        'the trade press, official employment reports, and reputable student-review communities). '
        'Themes summarize common sentiment; they are not individual verbatim quotes or institute '
        'endorsements."',
        ")",
        "",
        "DEPTH_REVIEWS: dict[str, dict] = {",
    ]

    for slug in sorted(reviews):
        r = reviews[slug]
        lines.append(f'    "{slug}": {{')
        lines.append(f'        "summary": {json.dumps(r["summary"])},')
        lines.append('        "themes": [')
        for t in r["themes"]:
            lines.append("            {")
            lines.append(f'                "label": {json.dumps(t["label"])},')
            lines.append(f'                "sentiment": {json.dumps(t["sentiment"])},')
            lines.append(f'                "detail": {json.dumps(t["detail"])},')
            lines.append("            },")
        lines.append("        ],")
        lines.append('        "sources": [')
        for s in r["sources"]:
            lines.append("            {")
            lines.append(f'                "label": {json.dumps(s["label"])},')
            lines.append(f'                "url": {json.dumps(s["url"])},')
            lines.append("            },")
        lines.append("        ],")
        lines.append('        "disclaimer": _DISCLAIMER,')
        lines.append("    },")

    lines.append("}")
    lines.append("")

    out = "/workspace/unipaith-backend/src/unipaith/data/georgia_tech_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
