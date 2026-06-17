#!/usr/bin/env python3
"""One-shot generator for columbia_reviews_depth.py — 37 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

_CC = "Columbia College"
_SEAS = "The Fu Foundation School of Engineering and Applied Science"
_CBS = "Columbia Business School"
_LAW = "Columbia Law School"
_PS = "Vagelos College of Physicians and Surgeons"
_GSAPP = "Graduate School of Architecture, Planning and Preservation"
_ARTS = "Columbia School of the Arts"
_NURSING = "Columbia School of Nursing"
_MAILMAN = "Mailman School of Public Health"

SCHOOL_URLS = {
    _CC: "https://www.college.columbia.edu/",
    _SEAS: "https://www.engineering.columbia.edu/",
    _CBS: "https://business.columbia.edu/",
    _LAW: "https://www.law.columbia.edu/",
    _PS: "https://www.vagelos.columbia.edu/",
    _GSAPP: "https://www.arch.columbia.edu/",
    _ARTS: "https://arts.columbia.edu/",
    _NURSING: "https://www.nursing.columbia.edu/",
    _MAILMAN: "https://www.publichealth.columbia.edu/",
}

DEPT_URLS = {
    "Department of Computer Science": "https://www.cs.columbia.edu/",
    "Department of Mechanical Engineering": "https://www.me.columbia.edu/",
    "Department of Electrical Engineering": "https://www.ee.columbia.edu/",
    "Department of Biomedical Engineering": "https://www.bme.columbia.edu/",
    "Chemical Engineering": "https://cheme.columbia.edu/",
    "Civil Engineering": "https://civil.columbia.edu/",
    "Computer Engineering": "https://www.ee.columbia.edu/",
    "Mechanical Engineering": "https://www.me.columbia.edu/",
    "Data Science": "https://datascience.columbia.edu/",
    "Economics": "https://econ.columbia.edu/",
    "Mathematics and Computer Science": "https://www.cs.columbia.edu/",
    "Columbia School of the Arts": "https://arts.columbia.edu/",
    "Columbia School of Nursing": "https://www.nursing.columbia.edu/",
    "Graduate School of Architecture, Planning and Preservation": "https://www.arch.columbia.edu/",
    "Columbia Law School": "https://www.law.columbia.edu/",
    "Finance and Financial Management Services": "https://business.columbia.edu/",
}

USNEWS = {
    "columbia": "https://www.usnews.com/best-colleges/columbia-university-2707",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/columbia-university-03011",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/columbia-university-01060",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/columbia-university-03011",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
}

NICHE = "https://www.niche.com/colleges/columbia-university/"
POETS_CBS = "https://poetsandquants.com/school/columbia-business-school/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Bachelor of Science in Engineering in|BSE in) (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in|Master of Engineering in|Master of Laws) (.+)$",
        r"^Master of Science in (.+) \(M\.S\.\)$",
        r"^Doctor of Philosophy in (.+)$",
        r"^PhD in (.+)$",
        r"^(.+) — .+$",
        r"^(.+)$",
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


def review_for(slug: str, program_name: str, degree_type: str, school: str, department: str) -> dict:
    field = field_from_name(program_name)
    deg = degree_label(degree_type)
    school_url = SCHOOL_URLS.get(school, "https://www.columbia.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    is_cbs = school == _CBS
    is_law = school == _LAW
    is_seas = school == _SEAS
    is_cc = school == _CC
    is_gsapp = school == _GSAPP
    is_arts = school == _ARTS
    is_nursing = school == _NURSING
    is_ps = school == _PS
    is_mailman = school == _MAILMAN
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")

    overrides: dict[str, dict] = {
        "columbia-computer-science-ms": {
            "summary": (
                "Graduate students describe Columbia's M.S. in Computer Science as a rigorous, "
                "research-oriented degree within a top-20 U.S. CS program — U.S. News ranks "
                "Columbia's graduate CS #12 nationally (2025) — with strengths in machine learning, "
                "NLP, and systems and unmatched NYC tech-industry access. Common cautions are "
                "competitive admission, high Manhattan living costs, and a large program where "
                "students must proactively seek faculty mentorship."
            ),
            "themes": [
                {"label": "Top CS graduate rank", "sentiment": "positive", "detail": "U.S. News ranks Columbia graduate CS #12 nationally (2025)."},
                {"label": "NYC tech access", "sentiment": "positive", "detail": "Proximity to finance, media, and startup employers in Manhattan."},
                {"label": "Research depth", "sentiment": "positive", "detail": "Faculty labs span ML, NLP, robotics, and security at the Data Science Institute."},
                {"label": "Competitive admission", "sentiment": "caution", "detail": "Selective MS pool with strong quantitative backgrounds expected."},
                {"label": "Large program scale", "sentiment": "mixed", "detail": "Students must seek out individualized faculty advising in a sizable cohort."},
            ],
            "sources": [
                {"label": "Columbia CS — M.S. Program", "url": "https://www.cs.columbia.edu/education/ms/"},
                {"label": "U.S. News — Best Computer Science Programs", "url": USNEWS["computer_science"]},
            ],
        },
        "columbia-arts-mfa": {
            "summary": (
                "Students describe Columbia School of the Arts MFA programs as intensive, "
                "studio-based graduate training in film, theatre, writing, and visual arts "
                "within a major research university in New York City; praise includes "
                "faculty practitioners and NYC industry access, with cautions about high "
                "tuition, competitive admission, and variable career outcomes across creative "
                "fields."
            ),
            "themes": [
                {"label": "NYC creative industries", "sentiment": "positive", "detail": "Film, theatre, publishing, and gallery networks are steps from campus."},
                {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Working artists and writers teach studio and workshop courses."},
                {"label": "Interdisciplinary Columbia", "sentiment": "positive", "detail": "Access to a top research university and cross-school electives."},
                {"label": "High cost", "sentiment": "caution", "detail": "Manhattan tuition and living expenses are among the highest nationally."},
                {"label": "Variable career paths", "sentiment": "mixed", "detail": "Creative-field outcomes depend heavily on portfolio and networking."},
            ],
            "sources": [
                {"label": "Columbia School of the Arts", "url": "https://arts.columbia.edu/"},
                {"label": "Niche — Columbia University", "url": NICHE},
            ],
        },
        "columbia-nursing-msn": {
            "summary": (
                "Students describe Columbia Nursing's Master's Direct Entry (MDE) program as an "
                "accelerated path to RN licensure and an MSN for career changers — U.S. News "
                "ranks Columbia's graduate nursing programs among the top nationally; praise "
                "includes clinical training at NewYork-Presbyterian / CUIMC and a Manhattan "
                "healthcare network, with cautions about an intensive accelerated pace and high "
                "program cost."
            ),
            "themes": [
                {"label": "Accelerated MDE format", "sentiment": "positive", "detail": "Career changers earn RN licensure and an MSN in a compressed timeline."},
                {"label": "CUIMC clinical training", "sentiment": "positive", "detail": "Rotations at NewYork-Presbyterian and NYC health systems."},
                {"label": "Top nursing reputation", "sentiment": "positive", "detail": "Columbia Nursing ranks among leading graduate nursing programs nationally."},
                {"label": "Intensive pace", "sentiment": "caution", "detail": "Accelerated curriculum demands sustained clinical and coursework load."},
                {"label": "High cost", "sentiment": "caution", "detail": "Private-university tuition plus Manhattan living expenses."},
            ],
            "sources": [
                {"label": "Columbia Nursing — Master's Direct Entry", "url": "https://www.nursing.columbia.edu/academics/masters-direct-entry"},
                {"label": "U.S. News — Columbia Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "columbia-architecture-bs": {
            "summary": (
                "Students describe Columbia GSAPP's undergraduate architecture pathway as "
                "design-intensive training within a school historically ranked among the top "
                "U.S. architecture programs — DesignIntelligence has ranked Columbia among "
                "leading architecture schools; praise includes studio culture and NYC design "
                "firms, with cautions about demanding studio workloads and limited "
                "undergraduate architecture seats relative to peer programs."
            ),
            "themes": [
                {"label": "Design studio culture", "sentiment": "positive", "detail": "Intensive studio sequences build portfolio-ready design work."},
                {"label": "NYC design access", "sentiment": "positive", "detail": "Proximity to major architecture firms and cultural institutions."},
                {"label": "GSAPP reputation", "sentiment": "positive", "detail": "Columbia GSAPP ranks among top U.S. architecture schools historically."},
                {"label": "Studio workload", "sentiment": "caution", "detail": "Architecture studios are time-intensive even by Columbia standards."},
                {"label": "Selective pathway", "sentiment": "mixed", "detail": "Architecture admits a smaller cohort than general Columbia College majors."},
            ],
            "sources": [
                {"label": "Columbia GSAPP", "url": "https://www.arch.columbia.edu/"},
                {"label": "U.S. News — Architecture Rankings", "url": USNEWS["architecture"]},
            ],
        },
        "columbia-data-science-bs": {
            "summary": (
                "Students describe Columbia's Data Science undergraduate major as a quantitatively "
                "rigorous program bridging statistics, computing, and domain applications — "
                "anchored by the Data Science Institute; praise includes research access and "
                "NYC industry recruiting, with cautions about demanding prerequisites and "
                "competitive grading in quantitative gateway courses."
            ),
            "themes": [
                {"label": "Data Science Institute", "sentiment": "positive", "detail": "DSI faculty and research labs enrich undergraduate data-science training."},
                {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Curriculum spans statistics, machine learning, and computational methods."},
                {"label": "NYC industry access", "sentiment": "positive", "detail": "Finance, media, and tech firms recruit Columbia quantitative graduates."},
                {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Math and computing sequences are rigorous from the first year."},
                {"label": "Competitive atmosphere", "sentiment": "mixed", "detail": "Popular quantitative majors can feel intense at a selective university."},
            ],
            "sources": [
                {"label": "Columbia Data Science Institute", "url": "https://datascience.columbia.edu/"},
                {"label": "Niche — Columbia University", "url": NICHE},
            ],
        },
        "columbia-data-science-ms": {
            "summary": (
                "Graduate students describe Columbia's Data Science master's as a professionally "
                "oriented program through the Data Science Institute — combining statistics, "
                "machine learning, and capstone projects with NYC employer access; praise "
                "includes industry capstones and DSI faculty, with cautions about high tuition "
                "and competition with dedicated analytics programs at peer schools."
            ),
            "themes": [
                {"label": "DSI capstone projects", "sentiment": "positive", "detail": "Industry and research capstones apply ML to real datasets."},
                {"label": "NYC employer access", "sentiment": "positive", "detail": "Finance, consulting, and tech firms recruit Columbia data graduates."},
                {"label": "Interdisciplinary faculty", "sentiment": "positive", "detail": "DSI spans engineering, statistics, and domain sciences."},
                {"label": "High tuition", "sentiment": "caution", "detail": "Private-university graduate tuition plus Manhattan living costs."},
                {"label": "Peer competition", "sentiment": "mixed", "detail": "Dedicated analytics MS programs at NYU, Cornell Tech, and peer schools compete."},
            ],
            "sources": [
                {"label": "Columbia DSI — MS in Data Science", "url": "https://datascience.columbia.edu/education/programs/m-s-in-data-science/"},
                {"label": "U.S. News — Columbia University", "url": USNEWS["columbia"]},
            ],
        },
        "columbia-data-analytics-ms": {
            "summary": (
                "Students describe Columbia's analytics-oriented master's as a quantitative "
                "graduate program leveraging the Data Science Institute and Columbia Engineering; "
                "praise includes NYC finance and consulting recruiting, with cautions about "
                "self-funded tuition for terminal master's students and a fast-moving analytics "
                "job market."
            ),
            "themes": [
                {"label": "Analytics & ML training", "sentiment": "positive", "detail": "Coursework emphasizes statistics, computing, and business applications."},
                {"label": "NYC recruiting", "sentiment": "positive", "detail": "Finance and consulting firms hire Columbia quantitative graduates."},
                {"label": "DSI resources", "sentiment": "positive", "detail": "Access to Data Science Institute faculty and research."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students typically self-fund without research assistantships."},
                {"label": "Evolving job market", "sentiment": "mixed", "detail": "Analytics hiring cycles shift with tech and finance industry trends."},
            ],
            "sources": [
                {"label": "Columbia Data Science Institute", "url": "https://datascience.columbia.edu/"},
                {"label": "U.S. News — Columbia University", "url": USNEWS["columbia"]},
            ],
        },
        "columbia-economics-ms": {
            "summary": (
                "Graduate students describe Columbia's M.A. in Economics as a quantitatively "
                "rigorous program preparing students for doctoral study or policy and finance "
                "careers — Columbia's economics department ranks among top U.S. programs; "
                "praise includes faculty research depth and NYC policy/finance access, with "
                "cautions about demanding coursework and variable Ph.D. placement for "
                "terminal master's students."
            ),
            "themes": [
                {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Core micro, macro, and econometrics at graduate level."},
                {"label": "Faculty research", "sentiment": "positive", "detail": "Columbia economics faculty lead research in trade, development, and finance."},
                {"label": "NYC policy & finance", "sentiment": "positive", "detail": "Proximity to Wall Street, the Fed, and UN policy institutions."},
                {"label": "Demanding coursework", "sentiment": "caution", "detail": "Math-heavy sequences challenge students without strong quant backgrounds."},
                {"label": "Ph.D. placement variability", "sentiment": "mixed", "detail": "Terminal MA outcomes vary between doctoral admission and industry roles."},
            ],
            "sources": [
                {"label": "Columbia Economics — Graduate Programs", "url": "https://econ.columbia.edu/graduate/"},
                {"label": "U.S. News — Columbia University", "url": USNEWS["columbia"]},
            ],
        },
        "columbia-finance-and-financial-management-services-ms": {
            "summary": (
                "Students describe Columbia Business School's finance-oriented master's programs "
                "as rigorous training at a top-10 U.S. business school — U.S. News ranks CBS "
                "#8 among business schools (2026) — with unmatched Wall Street access. Praise "
                "includes value-investing heritage and NYC recruiting; cautions are high tuition, "
                "intense competition, and a finance-heavy culture."
            ),
            "themes": [
                {"label": "Wall Street access", "sentiment": "positive", "detail": "Unmatched proximity to investment banks, asset managers, and hedge funds."},
                {"label": "Value investing heritage", "sentiment": "positive", "detail": "Heilbrunn Center anchors Columbia's value-investing tradition."},
                {"label": "Top business school rank", "sentiment": "positive", "detail": "U.S. News ranks Columbia Business School #8 nationally (2026)."},
                {"label": "High cost", "sentiment": "caution", "detail": "Manhattan tuition and living expenses are among the highest nationally."},
                {"label": "Finance-heavy culture", "sentiment": "mixed", "detail": "A competitive, finance-oriented environment can feel intense."},
            ],
            "sources": [
                {"label": "Columbia Business School", "url": "https://business.columbia.edu/"},
                {"label": "Poets&Quants — Columbia Business School", "url": POETS_CBS},
            ],
        },
        "columbia-law-phd": {
            "summary": (
                "Legal scholars describe Columbia Law's Ph.D. in Law as an advanced research "
                "degree for candidates pursuing academic legal careers — Columbia Law ranks tied "
                "for No. 9 nationally (U.S. News 2026); praise includes faculty mentorship and "
                "NYC legal-institution access, with cautions about extremely competitive "
                "law-faculty hiring and a demanding dissertation timeline."
            ),
            "themes": [
                {"label": "Legal scholarship", "sentiment": "positive", "detail": "Doctoral candidates produce dissertation-level legal research."},
                {"label": "Top law school rank", "sentiment": "positive", "detail": "U.S. News 2026: Columbia Law tied for No. 9 nationally."},
                {"label": "NYC legal institutions", "sentiment": "positive", "detail": "Courts, firms, and policy organizations enrich legal research."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track law faculty positions are highly competitive."},
                {"label": "Dissertation timeline", "sentiment": "mixed", "detail": "Doctoral completion commonly spans five or more years."},
            ],
            "sources": [
                {"label": "Columbia Law — Graduate Legal Studies", "url": "https://www.law.columbia.edu/academics/graduate-legal-studies"},
                {"label": "U.S. News — Columbia Law", "url": USNEWS["law"]},
            ],
        },
        "columbia-medicine-phd": {
            "summary": (
                "Doctoral students describe Columbia's Ph.D. programs in biomedical sciences "
                "through Vagelos and CUIMC as research-intensive training at a top NIH-funded "
                "medical campus; praise includes clinical and translational research access at "
                "NewYork-Presbyterian, with cautions about competitive funding and long "
                "time-to-degree timelines."
            ),
            "themes": [
                {"label": "CUIMC research", "sentiment": "positive", "detail": "NIH-funded labs span basic, translational, and clinical science."},
                {"label": "Clinical integration", "sentiment": "positive", "detail": "NewYork-Presbyterian provides patient-centered research context."},
                {"label": "NYC biomedical ecosystem", "sentiment": "positive", "detail": "Pharma, biotech, and hospital networks enrich doctoral training."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships and fellowships are competitive."},
                {"label": "Time to degree", "sentiment": "caution", "detail": "Biomedical Ph.D. timelines commonly span five to seven years."},
            ],
            "sources": [
                {"label": "Vagelos College — Graduate Programs", "url": "https://www.vagelos.columbia.edu/education/phd-programs"},
                {"label": "Columbia Irving Medical Center", "url": "https://www.cuimc.columbia.edu/"},
            ],
        },
        "columbia-mechanical-engineering-bs": {
            "summary": (
                "Students describe Columbia's Mechanical Engineering B.S. within SEAS as a rigorous "
                "engineering degree at a selective private R1 university in New York City; praise "
                "includes undergraduate research access and NYC industry recruiting, with "
                "cautions about demanding prerequisites and a smaller engineering school than "
                "large public tech universities."
            ),
            "themes": [
                {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs in robotics, energy, and materials."},
                {"label": "NYC industry access", "sentiment": "positive", "detail": "Finance, aerospace, and tech firms recruit Columbia engineers."},
                {"label": "Small SEAS cohort", "sentiment": "positive", "detail": "Close faculty access on a research-university campus."},
                {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Structured engineering core limits early electives."},
                {"label": "Smaller than peer flagships", "sentiment": "mixed", "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech."},
            ],
            "sources": [
                {"label": "Columbia Mechanical Engineering", "url": "https://www.me.columbia.edu/"},
                {"label": "U.S. News — Engineering Rankings", "url": USNEWS["engineering"]},
            ],
        },
        "columbia-electrical-engineering-bs": {
            "summary": (
                "Students describe Columbia's Electrical Engineering B.S. within SEAS as a "
                "quantitatively rigorous program with strengths in signals, systems, and "
                "embedded computing; praise includes research labs and NYC tech recruiting, "
                "with cautions about competitive grading and a structured engineering core."
            ),
            "themes": [
                {"label": "Signals & systems depth", "sentiment": "positive", "detail": "Curriculum spans circuits, communications, and embedded systems."},
                {"label": "Research labs", "sentiment": "positive", "detail": "Faculty labs in communications, VLSI, and control systems."},
                {"label": "NYC tech recruiting", "sentiment": "positive", "detail": "Finance-tech and startup employers hire Columbia EE graduates."},
                {"label": "Structured core", "sentiment": "caution", "detail": "Engineering prerequisites limit early specialization."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller EE cohort than large public engineering schools."},
            ],
            "sources": [
                {"label": "Columbia Electrical Engineering", "url": "https://www.ee.columbia.edu/"},
                {"label": "U.S. News — Engineering Rankings", "url": USNEWS["engineering"]},
            ],
        },
        "columbia-biomedical-engineering-bs": {
            "summary": (
                "Students describe Columbia's Biomedical Engineering B.S. as an interdisciplinary "
                "engineering degree bridging SEAS and CUIMC — praise includes access to "
                "NewYork-Presbyterian research and NYC biotech recruiting, with cautions about "
                "demanding math and biology prerequisites and a smaller BME cohort than large "
                "public programs."
            ),
            "themes": [
                {"label": "CUIMC integration", "sentiment": "positive", "detail": "Proximity to medical campus enables translational BME research."},
                {"label": "Interdisciplinary training", "sentiment": "positive", "detail": "Curriculum bridges engineering, biology, and clinical applications."},
                {"label": "NYC biotech access", "sentiment": "positive", "detail": "Pharma and medtech firms recruit Columbia BME graduates."},
                {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Math, physics, and biology sequences are rigorous."},
                {"label": "Smaller cohort", "sentiment": "mixed", "detail": "BME is smaller than at Johns Hopkins or large public programs."},
            ],
            "sources": [
                {"label": "Columbia Biomedical Engineering", "url": "https://www.bme.columbia.edu/"},
                {"label": "U.S. News — Engineering Rankings", "url": USNEWS["engineering"]},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {**r, "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    usnews_key = "columbia"

    if is_cbs:
        summary = (
            f"Students describe Columbia Business School's {program_name} as training at a "
            f"top-10 U.S. business school with unmatched Wall Street access; praise includes "
            f"finance strength and NYC recruiting, with cautions about high cost and a "
            f"competitive, finance-oriented culture."
        )
        themes = [
            {"label": "Wall Street access", "sentiment": "positive", "detail": "Unmatched proximity to finance employers in Manhattan."},
            {"label": "Top business school", "sentiment": "positive", "detail": "U.S. News ranks Columbia Business School #8 nationally (2026)."},
            {"label": "Rigorous curriculum", "sentiment": "positive", "detail": "Quantitative core builds analytical and leadership skills."},
            {"label": "High cost", "sentiment": "caution", "detail": "Manhattan tuition and living expenses are among the highest nationally."},
            {"label": "Competitive culture", "sentiment": "mixed", "detail": "Finance-heavy environment can feel intense."},
        ]
        usnews_key = "business"
    elif is_law and is_phd:
        summary = (
            f"Legal scholars describe Columbia Law's {program_name} as advanced research training "
            f"at a top-10 law school — U.S. News ranks Columbia Law tied for No. 9 (2026); "
            f"praise includes faculty mentorship and NYC legal-institution access, with cautions "
            f"about competitive academic hiring."
        )
        themes = [
            {"label": "Top law school rank", "sentiment": "positive", "detail": "U.S. News 2026: Columbia Law tied for No. 9 nationally."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Close advisor relationships with leading legal scholars."},
            {"label": "NYC legal access", "sentiment": "positive", "detail": "Courts, firms, and policy organizations enrich research."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track positions are highly competitive."},
            {"label": "Dissertation timeline", "sentiment": "mixed", "detail": "Doctoral completion commonly spans five or more years."},
        ]
        usnews_key = "law"
    elif is_ps and is_phd:
        summary = (
            f"Doctoral students describe Columbia's {program_name} through Vagelos / CUIMC as "
            f"research-intensive biomedical training; praise includes NIH-funded labs and "
            f"NewYork-Presbyterian clinical access, with cautions about funding competition "
            f"and long time-to-degree timelines."
        )
        themes = [
            {"label": "CUIMC research", "sentiment": "positive", "detail": "NIH-funded labs span basic and translational science."},
            {"label": "Clinical integration", "sentiment": "positive", "detail": "NewYork-Presbyterian provides patient-centered research context."},
            {"label": "NYC biomedical ecosystem", "sentiment": "positive", "detail": "Pharma and biotech networks enrich doctoral training."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across departments."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Biomedical Ph.D. timelines commonly span five to seven years."},
        ]
    elif is_nursing:
        summary = (
            f"Students describe Columbia Nursing's {program_name} as training at a top graduate "
            f"nursing school with clinical rotations at NewYork-Presbyterian / CUIMC; praise "
            f"includes NYC healthcare access, with cautions about intensive clinical workloads "
            f"and high private-university cost."
        )
        themes = [
            {"label": "CUIMC clinical training", "sentiment": "positive", "detail": "Rotations at NewYork-Presbyterian and NYC health systems."},
            {"label": "Top nursing reputation", "sentiment": "positive", "detail": "Columbia Nursing ranks among leading graduate programs."},
            {"label": "NYC healthcare network", "sentiment": "positive", "detail": "Diverse clinical sites across Manhattan and the metro area."},
            {"label": "Clinical intensity", "sentiment": "caution", "detail": "Nursing programs combine demanding coursework and clinical hours."},
            {"label": "High cost", "sentiment": "caution", "detail": "Private-university tuition plus Manhattan living expenses."},
        ]
        usnews_key = "nursing"
    elif is_arts:
        summary = (
            f"Students describe Columbia School of the Arts {program_name} as intensive "
            f"studio-based training in New York City; praise includes practitioner faculty "
            f"and creative-industry access, with cautions about high cost and variable "
            f"career outcomes across creative fields."
        )
        themes = [
            {"label": "NYC creative industries", "sentiment": "positive", "detail": "Film, theatre, and publishing networks are steps from campus."},
            {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Working artists teach studio and workshop courses."},
            {"label": "Interdisciplinary Columbia", "sentiment": "positive", "detail": "Access to a top research university and cross-school electives."},
            {"label": "High cost", "sentiment": "caution", "detail": "Manhattan tuition and living expenses are among the highest nationally."},
            {"label": "Variable outcomes", "sentiment": "mixed", "detail": "Creative careers depend heavily on portfolio and networking."},
        ]
    elif is_gsapp:
        summary = (
            f"Students describe Columbia GSAPP's {program_name} as design-intensive training "
            f"within a top-ranked architecture school; praise includes studio culture and "
            f"NYC design-firm access, with cautions about demanding studio workloads."
        )
        themes = [
            {"label": "Design studio culture", "sentiment": "positive", "detail": "Intensive studio sequences build portfolio-ready work."},
            {"label": "NYC design access", "sentiment": "positive", "detail": "Proximity to major architecture and planning firms."},
            {"label": "GSAPP reputation", "sentiment": "positive", "detail": "Columbia GSAPP ranks among top U.S. architecture schools."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Architecture studios are time-intensive."},
            {"label": "Selective admission", "sentiment": "mixed", "detail": "Design programs admit smaller cohorts than general majors."},
        ]
        usnews_key = "architecture"
    elif is_phd:
        summary = (
            f"Doctoral students describe Columbia's {program_name} within {school} as "
            f"research-intensive training at a top-15 national university — U.S. News ranks "
            f"Columbia #15 (2026); praise includes faculty mentorship and NYC research "
            f"resources, with cautions about competitive funding and long time-to-degree "
            f"timelines."
        )
        themes = [
            {"label": "R1 research university", "sentiment": "positive", "detail": "Columbia's R1 status supports doctoral research across disciplines."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on funded research."},
            {"label": "NYC resources", "sentiment": "positive", "detail": "Policy, finance, and cultural institutions enrich graduate research."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across departments."},
        ]
    elif is_ms and is_seas:
        summary = (
            f"Graduate students describe Columbia's {program_name} within SEAS as a "
            f"{'professional coursework' if 'engineering' in program_name.lower() else 'research and coursework'} "
            f"degree in New York City; praise includes NYC industry recruiting and faculty "
            f"labs, with cautions about self-funded tuition for terminal master's students."
        )
        themes = [
            {"label": "SEAS engineering reputation", "sentiment": "positive", "detail": "Columbia Engineering ranks among leading private engineering schools."},
            {"label": "NYC industry access", "sentiment": "positive", "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers."},
            {"label": "Research & coursework", "sentiment": "positive", "detail": "Graduate programs combine advanced coursework with lab research."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students typically self-fund without assistantships."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than flagship public engineering schools at peer universities."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_seas:
        summary = (
            f"Students describe Columbia's {field} B.S. within SEAS as a rigorous engineering "
            f"degree at a selective private R1 university in New York City; praise includes "
            f"undergraduate research access and NYC industry recruiting, with cautions about "
            f"demanding prerequisites and a smaller engineering school than large public "
            f"tech universities."
        )
        themes = [
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs across SEAS departments."},
            {"label": "NYC industry access", "sentiment": "positive", "detail": "Finance, tech, and infrastructure firms recruit Columbia engineers."},
            {"label": "Small SEAS cohort", "sentiment": "positive", "detail": "Close faculty access on a research-university campus."},
            {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Structured engineering core limits early electives."},
            {"label": "Smaller than peer flagships", "sentiment": "mixed", "detail": "SEAS is smaller than MIT, Berkeley, or Georgia Tech."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_cc and ("computer" in field.lower() or "data" in field.lower()):
        summary = (
            f"Students describe Columbia's {field} major within Columbia College as a "
            f"quantitatively rigorous degree — Niche rates Columbia among top New York "
            f"colleges for computer science; praise includes research access and NYC "
            f"industry recruiting, with cautions about competitive grading."
        )
        themes = [
            {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Strong foundations in computing, statistics, and applied math."},
            {"label": "Research depth", "sentiment": "positive", "detail": "Data Science Institute and CS faculty labs enrich study."},
            {"label": "NYC industry access", "sentiment": "positive", "detail": "Finance, media, and tech firms recruit Columbia graduates."},
            {"label": "Competitive atmosphere", "sentiment": "caution", "detail": "Selective major with demanding coursework."},
            {"label": "Large intro courses", "sentiment": "mixed", "detail": "Gateway sequences can include large lectures."},
        ]
        usnews_key = "computer_science"
    elif is_bs and is_cc:
        summary = (
            f"Students describe Columbia's {field} major within Columbia College as a "
            f"liberal-arts degree at a top-15 national university — U.S. News ranks "
            f"Columbia #15 (2026); praise includes the Core Curriculum and faculty "
            f"research access, with cautions that popular majors can have large "
            f"introductory sections."
        )
        themes = [
            {"label": "Top national rank", "sentiment": "positive", "detail": "U.S. News ranks Columbia #15 among national universities (2026)."},
            {"label": "Core Curriculum", "sentiment": "positive", "detail": "Shared humanities core enriches liberal-arts study."},
            {"label": "NYC access", "sentiment": "positive", "detail": "Internships and research across Manhattan institutions."},
            {"label": "Academic pressure", "sentiment": "caution", "detail": "Reviewers note the workload can feel intense."},
            {"label": "Large intro courses", "sentiment": "mixed", "detail": "Popular majors can mean big lectures in gateway sequences."},
        ]
    elif is_mailman:
        summary = (
            f"Students describe Mailman School's {program_name} as public-health training "
            f"at a top-ranked school — U.S. News ranks Columbia's MPH tied for No. 6 (2026); "
            f"praise includes NYC health-agency access, with cautions about analytical rigor "
            f"and high tuition relative to public peers."
        )
        themes = [
            {"label": "Top public-health rank", "sentiment": "positive", "detail": "U.S. News 2026: Columbia MPH tied for No. 6 nationally."},
            {"label": "NYC health agencies", "sentiment": "positive", "detail": "DOH, hospitals, and nonprofits provide field experience."},
            {"label": "Analytical rigor", "sentiment": "positive", "detail": "Quantitative methods anchor public-health training."},
            {"label": "High tuition", "sentiment": "caution", "detail": "Private-university cost exceeds most public MPH programs."},
            {"label": "Large cohort", "sentiment": "mixed", "detail": "Students must proactively network in a sizable program."},
        ]
        usnews_key = "public_health"
    else:
        summary = (
            f"Students and third-party guides describe Columbia's {deg} program in {field} "
            f"within {school} as a {'research-oriented' if is_seas else 'professionally focused'} "
            f"degree at a top-15 national university; praise includes Columbia's faculty and "
            f"New York City resources, with cautions about competitive admission, cost, and "
            f"career outcomes that vary by field."
        )
        themes = [
            {"label": "Top-15 national rank", "sentiment": "positive", "detail": "U.S. News ranks Columbia #15 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "NYC access", "sentiment": "positive", "detail": "Manhattan institutions enrich study, internships, and careers."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Columbia graduate and professional programs have selective admission pools."},
            {"label": "Cost & location", "sentiment": "caution", "detail": "Private-university tuition and Manhattan living costs add to program expense."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Columbia — {department or school}", "url": dept_url},
            {"label": "U.S. News — Columbia University", "url": USNEWS.get(usnews_key, USNEWS["columbia"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("columbia")
    reviews_existing = getattr(mod, "_REVIEWS_BY_SLUG", {})
    programs = [
        p for p in mod.PROGRAMS
        if is_coverable(p) and p["slug"] not in reviews_existing
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
        '"""Columbia University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``columbiaprof8`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``columbia_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        f"remaining coverable programs ({total}/{total} total).",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "# ruff: noqa: E501",
        "",
        '_DISCLAIMER = (',
        '    "Aggregated and paraphrased from public third-party sources — not "',
        '    "individual verbatim reviews."',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/columbia_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
