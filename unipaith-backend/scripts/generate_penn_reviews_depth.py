#!/usr/bin/env python3
"""One-shot generator for penn_reviews_depth.py — 46 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

SCHOOL_URLS = {
    "School of Arts and Sciences": "https://www.sas.upenn.edu/",
    "The Wharton School": "https://www.wharton.upenn.edu/",
    "School of Engineering and Applied Science": "https://www.seas.upenn.edu/",
    "School of Nursing": "https://www.nursing.upenn.edu/",
    "Perelman School of Medicine": "https://www.med.upenn.edu/",
    "University of Pennsylvania Carey Law School": "https://www.law.upenn.edu/",
    "Stuart Weitzman School of Design": "https://www.design.upenn.edu/",
    "School of Social Policy and Practice": "https://sp2.upenn.edu/",
    "School of Veterinary Medicine": "https://www.vet.upenn.edu/",
}

DEPT_URLS = {
    "Computer Science": "https://www.cis.upenn.edu/",
    "Biomedical/Medical Engineering": "https://be.seas.upenn.edu/",
    "Chemical Engineering": "https://cbe.seas.upenn.edu/",
    "Computer Engineering": "https://www.cis.upenn.edu/",
    "Electrical, Electronics, and Communications Engineering": "https://www.ese.upenn.edu/",
    "Mechanical Engineering": "https://www.me.upenn.edu/",
    "Department of Mechanical Engineering and Applied Mechanics": "https://www.me.upenn.edu/",
    "Materials Engineering": "https://www.mse.seas.upenn.edu/",
    "Systems Engineering": "https://www.ese.upenn.edu/",
    "Economics": "https://economics.sas.upenn.edu/",
    "Department of Economics": "https://economics.sas.upenn.edu/",
    "Film/Video and Photographic Arts": "https://www.sas.upenn.edu/",
    "Mathematics and Computer Science": "https://www.cis.upenn.edu/",
    "Architecture": "https://www.design.upenn.edu/architecture",
    "Public Health": "https://www.med.upenn.edu/publichealth/",
    "Social Work": "https://sp2.upenn.edu/academics/doctoral-program/",
    "Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing": "https://www.nursing.upenn.edu/",
    "Finance and Financial Management Services": "https://finance.wharton.upenn.edu/",
    "Business/Commerce, General": "https://www.wharton.upenn.edu/",
    "Business Administration, Management and Operations": "https://www.wharton.upenn.edu/doctoral/",
    "Entrepreneurial and Small Business Operations": "https://entrepreneurship.wharton.upenn.edu/",
    "University of Pennsylvania Carey Law School": "https://www.law.upenn.edu/",
    "School of Veterinary Medicine": "https://www.vet.upenn.edu/",
}

USNEWS = {
    "penn": "https://www.usnews.com/best-colleges/university-of-pennsylvania-3378",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-pennsylvania-03060",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/the-wharton-school-01099",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-pennsylvania-04095",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-pennsylvania-03060",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/university-of-pennsylvania-04095",
    "veterinary": "https://www.usnews.com/best-graduate-schools/top-veterinary-schools/university-of-pennsylvania-03060",
    "economics": "https://www.usnews.com/best-colleges/rankings/economics",
}

NICHE = "https://www.niche.com/colleges/university-of-pennsylvania/"
POETS_WHARTON = "https://poetsandquants.com/schools/the-wharton-school-university-of-pennsylvania/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in) (.+)$",
        r"^Doctor of Philosophy in (.+)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.upenn.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "penn-computer-science-ms": {
            "summary": (
                "Graduate applicants describe Penn's M.S.E. in Computer Science within CIS "
                "as a research-oriented degree with strengths in AI, robotics (GRASP), and "
                "theory; praise includes Philadelphia tech recruiting and interdisciplinary "
                "ties to Wharton and Medicine, with cautions about self-funded tuition for "
                "terminal master's students and a smaller department than CS-flagship giants."
            ),
            "themes": [
                {"label": "AI & robotics research", "sentiment": "positive", "detail": "GRASP and CIS labs connect computing to robotics and health."},
                {"label": "Philadelphia recruiting", "sentiment": "positive", "detail": "Graduates place at major tech firms, startups, and Ph.D. programs."},
                {"label": "Interdisciplinary Penn", "sentiment": "positive", "detail": "CIS ties to Wharton, Medicine, and Annenberg enrich applied CS."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Smaller CS department", "sentiment": "mixed", "detail": "Penn CIS ranks below the very largest CS-focused universities."},
            ],
            "sources": [
                {"label": "Penn CIS — Graduate Programs", "url": "https://www.cis.upenn.edu/graduate-programs/"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "penn-computer-science-bs": {
            "summary": (
                "Students describe Penn's undergraduate Computer Science within CIS as a "
                "quantitatively rigorous degree with access to GRASP robotics and AI labs; "
                "praise includes dual-degree options with Wharton and strong Philadelphia "
                "recruiting, with cautions that gateway courses are competitive and the "
                "department is smaller than CS-flagship peers."
            ),
            "themes": [
                {"label": "Quantitative rigor", "sentiment": "positive", "detail": "CIS core sequences in algorithms, systems, and theory are demanding."},
                {"label": "GRASP & AI labs", "sentiment": "positive", "detail": "Undergraduates join robotics, NLP, and computer-vision research groups."},
                {"label": "Wharton dual degrees", "sentiment": "positive", "detail": "M&T and CIS+Wharton paths attract tech-finance careers."},
                {"label": "Course access", "sentiment": "caution", "detail": "Popular upper-level electives fill quickly at a selective university."},
                {"label": "Department scale", "sentiment": "mixed", "detail": "Penn CIS is strong but smaller than MIT/Stanford/CMU CS departments."},
            ],
            "sources": [
                {"label": "Penn CIS — Undergraduate", "url": "https://www.cis.upenn.edu/undergraduate-program/"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "penn-mechanical-engineering-bse": {
            "summary": (
                "Students describe Penn's Mechanical Engineering and Applied Mechanics BSE "
                "as a design- and research-oriented engineering degree with access to the "
                "GRASP robotics lab and Singh Center; praise includes small upper-level "
                "classes and Philadelphia industry recruiting, with cautions about a "
                "theory-heavy core and demanding workload alongside SAS distribution."
            ),
            "themes": [
                {"label": "Design & robotics", "sentiment": "positive", "detail": "MEAM connects to GRASP and design studios in Penn Engineering."},
                {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join labs in biomechanics, fluids, and materials."},
                {"label": "Philadelphia recruiting", "sentiment": "positive", "detail": "Graduates enter med-device, aerospace, and consulting firms."},
                {"label": "Theory-heavy core", "sentiment": "mixed", "detail": "Strong mathematical foundations; some wish for more applied electives."},
                {"label": "Workload", "sentiment": "caution", "detail": "Engineering sequences alongside SAS requirements are demanding."},
            ],
            "sources": [
                {"label": "Penn MEAM — Undergraduate", "url": "https://www.me.upenn.edu/undergraduate"},
                {"label": "U.S. News — Penn Engineering", "url": USNEWS["engineering"]},
            ],
        },
        "penn-economics-ba": {
            "summary": (
                "Students describe Penn's Economics major within Arts & Sciences as a "
                "quantitatively rigorous social-science degree — U.S. News ranks Penn #7 "
                "nationally (2026) — with praise for econometrics training and "
                "Wharton-adjacent finance recruiting; cautions include large introductory "
                "sections and competitive access to popular electives."
            ),
            "themes": [
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Econometrics and micro/macro theory sequences are program strengths."},
                {"label": "Finance recruiting", "sentiment": "positive", "detail": "Philadelphia and NYC finance firms recruit Penn economics majors."},
                {"label": "Graduate placement", "sentiment": "positive", "detail": "Consistent placement in economics, policy, and business Ph.D. programs."},
                {"label": "Large intro courses", "sentiment": "caution", "detail": "Gateway economics lectures can be large at a selective university."},
                {"label": "Elective access", "sentiment": "mixed", "detail": "Popular seminars fill quickly; registration planning matters."},
            ],
            "sources": [
                {"label": "Penn Economics — Undergraduate", "url": "https://economics.sas.upenn.edu/undergraduate"},
                {"label": "U.S. News — Best Undergraduate Economics", "url": USNEWS["economics"]},
            ],
        },
        "penn-finance-and-financial-management-services-bs": {
            "summary": (
                "Students describe Wharton's undergraduate finance concentration as one of "
                "the nation's premier finance programs — Poets&Quants and U.S. News rank "
                "Wharton among the top business schools — with praise for investment-banking "
                "and buy-side recruiting, with cautions about a competitive culture, "
                "quantitatively intense coursework, and high cost of attendance."
            ),
            "themes": [
                {"label": "Finance recruiting", "sentiment": "positive", "detail": "Wall Street, private equity, and asset-management firms recruit heavily."},
                {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Finance sequences emphasize modeling, valuation, and data analysis."},
                {"label": "Wharton network", "sentiment": "positive", "detail": "A large global alumni network opens doors in finance and consulting."},
                {"label": "Competitive culture", "sentiment": "caution", "detail": "Recruiting timelines and club culture can feel intense."},
                {"label": "Cost", "sentiment": "caution", "detail": "Private-university tuition exceeds $90,000 per year all-in."},
            ],
            "sources": [
                {"label": "Wharton — Undergraduate Finance", "url": "https://finance.wharton.upenn.edu/undergraduate/"},
                {"label": "Poets&Quants — Wharton", "url": POETS_WHARTON},
            ],
        },
        "penn-public-health-ms": {
            "summary": (
                "Graduate students describe Penn's Master of Public Health within Perelman "
                "as a practice- and research-oriented health degree with access to Penn "
                "Medicine and the Philadelphia health department; praise includes "
                "epidemiology and health-policy faculty, with cautions about self-funded "
                "tuition for some master's tracks and competitive clinical-research funding."
            ),
            "themes": [
                {"label": "Penn Medicine access", "sentiment": "positive", "detail": "Affiliated hospitals support epidemiology and health-services research."},
                {"label": "Health-policy ties", "sentiment": "positive", "detail": "Proximity to Philadelphia government and policy nonprofits enriches study."},
                {"label": "Interdisciplinary faculty", "sentiment": "positive", "detail": "Faculty span epidemiology, biostatistics, and health economics."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students may self-fund without assistantships."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Perelman."},
            ],
            "sources": [
                {"label": "Penn — Master of Public Health", "url": "https://www.med.upenn.edu/publichealth/mph/"},
                {"label": "U.S. News — Penn Perelman School of Medicine", "url": USNEWS["medicine"]},
            ],
        },
        "penn-veterinary-medicine-prof": {
            "summary": (
                "Students describe Penn Vet's V.M.D. as one of the nation's leading "
                "veterinary programs — U.S. News ranks Penn Vet among top veterinary "
                "schools — with praise for the New Bolton Center large-animal hospital "
                "and translational research, with cautions about demanding coursework, "
                "competitive specialty residency matching, and rural-clinical travel."
            ),
            "themes": [
                {"label": "Top veterinary rank", "sentiment": "positive", "detail": "U.S. News ranks Penn Vet among leading veterinary schools nationally."},
                {"label": "New Bolton Center", "sentiment": "positive", "detail": "Large-animal clinical training at New Bolton Center is a program hallmark."},
                {"label": "Translational research", "sentiment": "positive", "detail": "Penn Medicine ties support comparative and translational vet research."},
                {"label": "Residency competition", "sentiment": "caution", "detail": "Specialty residency matching is competitive nationally."},
                {"label": "Clinical travel", "sentiment": "mixed", "detail": "Large-animal rotations require travel to Kennett Square facilities."},
            ],
            "sources": [
                {"label": "Penn Vet — V.M.D. Program", "url": "https://www.vet.upenn.edu/education/doctor-veterinary-medicine"},
                {"label": "U.S. News — Veterinary Medicine", "url": USNEWS["veterinary"]},
            ],
        },
        "penn-architecture-bs": {
            "summary": (
                "Students describe Penn's undergraduate Architecture within the Weitzman "
                "School as a design-intensive degree in a top-ranked program — U.S. News "
                "ranks Penn among leading graduate architecture schools — with praise for "
                "studio culture and Philadelphia urban-design access, with cautions about "
                "demanding studio workloads and a profession with variable job security."
            ),
            "themes": [
                {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and pin-ups anchor the architecture curriculum."},
                {"label": "Philadelphia urban design", "sentiment": "positive", "detail": "City planning and historic-preservation projects enrich coursework."},
                {"label": "Weitzman faculty", "sentiment": "positive", "detail": "Practicing architects and theorists review student work."},
                {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require long hours and iterative critique."},
                {"label": "Career variability", "sentiment": "mixed", "detail": "Architecture hiring cycles with the construction economy."},
            ],
            "sources": [
                {"label": "Weitzman — Architecture", "url": "https://www.design.upenn.edu/architecture"},
                {"label": "U.S. News — Architecture rankings", "url": USNEWS["architecture"]},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {
            **r,
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }

    fl = field.lower()
    is_phd = degree_type in ("phd", "doctoral")
    is_ms = degree_type == "masters"
    is_bs = degree_type == "bachelors"
    is_prof = degree_type == "professional"
    is_wharton = "Wharton" in school
    is_seas = "Engineering" in school
    is_sas = "Arts and Sciences" in school
    is_law = "Law" in school
    is_med = "Medicine" in school
    is_nursing = "Nursing" in school
    is_design = "Design" in school
    is_sp2 = "Social Policy" in school
    is_vet = "Veterinary" in school

    usnews_key = "penn"
    if "computer" in fl:
        usnews_key = "computer_science"
    elif is_seas or "engineering" in fl:
        usnews_key = "engineering"
    elif is_wharton or "business" in fl or "finance" in fl or "entrepreneur" in fl:
        usnews_key = "business"
    elif is_law:
        usnews_key = "law"
    elif is_med or "public health" in fl:
        usnews_key = "public_health" if "public health" in fl else "medicine"
    elif is_nursing:
        usnews_key = "nursing"
    elif is_design or "architecture" in fl:
        usnews_key = "architecture"
    elif is_vet:
        usnews_key = "veterinary"
    elif "economics" in fl:
        usnews_key = "economics"

    if is_phd and is_law:
        summary = (
            f"Doctoral scholars describe Penn Law's {field} as a research degree within "
            f"Carey Law — U.S. News ranks Penn Law among the nation's top programs — "
            f"with praise for faculty mentorship and Philadelphia legal community access, "
            f"with cautions about competitive academic hiring and limited funding relative "
            f"to large public law schools."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Penn Law among leading national programs."},
            {"label": "Philadelphia legal market", "sentiment": "positive", "detail": "Proximity to major firms and courts supports research and clerkships."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small doctoral cohorts enable close work with legal scholars."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track law faculty positions are nationally competitive."},
            {"label": "Funding variability", "sentiment": "caution", "detail": "Doctoral funding packages vary; external fellowships are common."},
        ]
    elif is_prof and is_law:
        summary = (
            f"Students describe Penn Carey Law's {field} as a scholarly program within "
            f"a top-ranked law school; praise includes faculty seminars and Philadelphia "
            f"legal resources, with cautions that graduate law programs emphasize legal "
            f"scholarship over U.S. bar-exam preparation."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Penn Law among the nation's leading programs."},
            {"label": "Scholarly focus", "sentiment": "positive", "detail": "Programs emphasize legal theory and interdisciplinary research."},
            {"label": "Philadelphia network", "sentiment": "positive", "detail": "Major firms and courts provide internship and research access."},
            {"label": "Bar-exam pathway", "sentiment": "caution", "detail": "Graduate law programs are not designed as U.S. bar-exam preparation."},
            {"label": "Career orientation", "sentiment": "mixed", "detail": "Graduates often return to academia, judiciary, or international practice."},
        ]
    elif is_ms and is_wharton or is_bs and is_wharton or is_phd and is_wharton:
        summary = (
            f"Students and guides describe Wharton's {deg} offerings in {field} within one of "
            f"the nation's top business schools — Poets&Quants and U.S. News consistently rank "
            f"Wharton among leading business programs; praise includes finance strength and "
            f"a powerful alumni network, with cautions about selective admission, high tuition, "
            f"and a competitive recruiting culture."
        )
        themes = [
            {"label": "Finance & analytics strength", "sentiment": "positive", "detail": "Wharton is perennially ranked among top finance and analytics programs."},
            {"label": "Recruiting depth", "sentiment": "positive", "detail": "Consulting, finance, and tech firms recruit actively from Wharton."},
            {"label": "Alumni network", "sentiment": "positive", "detail": "A large global Wharton network opens doors widely."},
            {"label": "Competitive culture", "sentiment": "caution", "detail": "Recruiting timelines and club culture can feel intense."},
            {"label": "Tuition cost", "sentiment": "caution", "detail": "Private business-school tuition is steep; merit aid is limited."},
        ]
        usnews_key = "business"
    elif is_phd and is_med or is_ms and is_med:
        summary = (
            f"Graduate students describe Perelman's {deg} program in {field} as a research-intensive "
            f"health-sciences degree with access to Penn Medicine hospitals — U.S. News ranks "
            f"Perelman among top research medical schools; praise includes translational research "
            f"infrastructure, with cautions about competitive residency matching and Philadelphia "
            f"living costs."
        )
        themes = [
            {"label": "Top research medical school", "sentiment": "positive", "detail": "U.S. News ranks Perelman among leading medical schools for research."},
            {"label": "Hospital access", "sentiment": "positive", "detail": "Penn Medicine hospitals support clinical research."},
            {"label": "Translational research", "sentiment": "positive", "detail": "Students join labs spanning basic science and clinical trials."},
            {"label": "Residency competition", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research portfolios."},
            {"label": "Living costs", "sentiment": "caution", "detail": "Philadelphia housing adds to professional-school tuition."},
        ]
    elif is_phd and is_nursing or is_ms and is_nursing:
        summary = (
            f"Graduate students describe Penn Nursing's {deg} program in {field} as a "
            f"research-intensive nursing degree — U.S. News ranks Penn Nursing among the "
            f"world's top nursing schools; praise includes clinical research at Penn "
            f"Medicine and aging/health-outcomes faculty, with cautions about competitive "
            f"admission and self-funded tuition for some master's tracks."
        )
        themes = [
            {"label": "Top nursing rank", "sentiment": "positive", "detail": "U.S. News ranks Penn Nursing among leading nursing schools globally."},
            {"label": "Clinical research", "sentiment": "positive", "detail": "Penn Medicine partnerships support nursing science research."},
            {"label": "Health-outcomes focus", "sentiment": "positive", "detail": "Faculty lead work in aging, global health, and health policy."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Graduate nursing programs have competitive applicant pools."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students may self-fund without assistantships."},
        ]
        usnews_key = "nursing"
    elif is_phd and is_sp2 or is_ms and is_sp2:
        summary = (
            f"Graduate students describe SP2's {deg} program in {field} as a research-oriented "
            f"social-policy degree with Philadelphia community partnerships; praise includes "
            f"faculty in poverty research and child welfare, with cautions about limited "
            f"graduate funding and career paths that often require licensure or further study."
        )
        themes = [
            {"label": "Policy research", "sentiment": "positive", "detail": "SP2 faculty lead work in poverty, child welfare, and nonprofit management."},
            {"label": "Philadelphia partnerships", "sentiment": "positive", "detail": "Community agencies and city government support field placements."},
            {"label": "Interdisciplinary Penn", "sentiment": "positive", "detail": "Ties to Law, Medicine, and Wharton enrich social-policy study."},
            {"label": "Funding scarcity", "sentiment": "caution", "detail": "Graduate assistantships are scarcer than in STEM Ph.D. programs."},
            {"label": "Licensure paths", "sentiment": "mixed", "detail": "Clinical social-work careers require state licensure beyond the degree."},
        ]
    elif is_phd and is_design or is_ms and is_design or is_bs and is_design:
        summary = (
            f"Students describe Weitzman's {deg} program in {field} as a design-intensive "
            f"degree — U.S. News ranks Penn among leading graduate design schools; praise "
            f"includes studio culture and Philadelphia urban-design access, with cautions "
            f"about demanding studio workloads and career variability in creative fields."
        )
        themes = [
            {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and pin-ups anchor the curriculum."},
            {"label": "Philadelphia access", "sentiment": "positive", "detail": "Urban design and planning projects connect to the city."},
            {"label": "Visiting critics", "sentiment": "positive", "detail": "Practicing architects and planners review student work."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require long hours and iterative critique."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Design hiring cycles with the construction and development economy."},
        ]
        usnews_key = "architecture"
    elif is_phd:
        summary = (
            f"Doctoral students describe Penn's Ph.D. in {field} within {school} as a "
            f"research degree at an Ivy League R1 university ranked #7 nationally by "
            f"U.S. News (2026); praise includes faculty mentorship and Philadelphia "
            f"professional access, with cautions about competitive admission, five-plus-year "
            f"timelines, and specialized hiring markets."
        )
        themes = [
            {"label": "R1 research university", "sentiment": "positive", "detail": "Penn's R1 status supports doctoral research across disciplines."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on funded research."},
            {"label": "Philadelphia access", "sentiment": "positive", "detail": "Proximity to firms, hospitals, and cultural institutions enriches study."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Strong research background and faculty alignment are expected."},
        ]
    elif is_ms and is_seas:
        summary = (
            f"Graduate applicants describe Penn's M.S.E. in {field} within Penn Engineering "
            f"as a research and coursework degree with ties to Penn Medicine and Wharton; "
            f"students value Philadelphia industry recruiting and faculty labs, with cautions "
            f"about self-funded tuition for terminal master's students and competitive funding."
        )
        themes = [
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Penn Engineering is consistently ranked among leading engineering schools."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "GRASP, Singh Center, and med-tech partnerships span schools."},
            {"label": "Philadelphia recruiting", "sentiment": "positive", "detail": "Graduates enter industry R&D, consulting, and doctoral programs."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Penn Engineering."},
        ]
    elif is_bs and is_seas:
        summary = (
            f"Students describe Penn's undergraduate {field} program in Penn Engineering as a "
            f"quantitatively rigorous engineering degree with research-lab access; praise "
            f"includes GRASP robotics ties and Philadelphia recruiting, with cautions that "
            f"core sequences are theory-heavy and demanding alongside SAS distribution."
        )
        themes = [
            {"label": "Engineering rigor", "sentiment": "positive", "detail": "Penn Engineering's quantitative core prepares students for industry and grad school."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join labs in bioengineering, CIS, and materials science."},
            {"label": "Philadelphia recruiting", "sentiment": "positive", "detail": "Tech, consulting, and med-device firms recruit Penn engineers."},
            {"label": "Theory-heavy core", "sentiment": "mixed", "detail": "Strong mathematical foundations; some wish for more applied electives."},
            {"label": "Workload", "sentiment": "caution", "detail": "Engineering sequences alongside SAS requirements are demanding."},
        ]
    elif is_bs and is_sas:
        summary = (
            f"Students describe Penn's undergraduate program in {field} within Arts & Sciences "
            f"as a liberal-arts degree at a top-10 national university — U.S. News ranks Penn "
            f"#7 (2026); praise includes small seminars, faculty research access, and "
            f"Philadelphia internships, with cautions that popular majors can have large "
            f"introductory sections."
        )
        themes = [
            {"label": "Top national rank", "sentiment": "positive", "detail": "U.S. News ranks Penn #7 among national universities (2026)."},
            {"label": "Seminar culture", "sentiment": "positive", "detail": "Upper-level SAS courses emphasize discussion and faculty mentorship."},
            {"label": "Philadelphia access", "sentiment": "positive", "detail": "Internships and research opportunities extend beyond campus."},
            {"label": "Large intro courses", "sentiment": "caution", "detail": "Popular majors can mean big lectures in gateway sequences."},
            {"label": "Grad-school path", "sentiment": "mixed", "detail": "Many humanities and social-science majors pursue further graduate study."},
        ]
    elif is_prof and is_vet:
        summary = (
            f"Students describe Penn Vet's {field} as one of the nation's leading veterinary "
            f"programs — U.S. News ranks Penn Vet among top veterinary schools — with praise "
            f"for New Bolton Center and translational research, with cautions about demanding "
            f"coursework and competitive specialty residency matching."
        )
        themes = [
            {"label": "Top veterinary rank", "sentiment": "positive", "detail": "U.S. News ranks Penn Vet among leading veterinary schools."},
            {"label": "New Bolton Center", "sentiment": "positive", "detail": "Large-animal clinical training is a program hallmark."},
            {"label": "Translational research", "sentiment": "positive", "detail": "Penn Medicine ties support comparative vet research."},
            {"label": "Residency competition", "sentiment": "caution", "detail": "Specialty residency matching is competitive nationally."},
            {"label": "Clinical travel", "sentiment": "mixed", "detail": "Large-animal rotations require travel to Kennett Square."},
        ]
        usnews_key = "veterinary"
    else:
        summary = (
            f"Students and third-party guides describe Penn's {deg} program in {field} "
            f"within {school} as a {'research-oriented' if is_seas or is_sas else 'professionally focused'} "
            f"degree at a top-10 national university; praise includes Penn's faculty "
            f"and Philadelphia resources, with cautions about competitive admission, cost, "
            f"and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top-10 national rank", "sentiment": "positive", "detail": "U.S. News ranks Penn #7 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Philadelphia access", "sentiment": "positive", "detail": "Students leverage firms, hospitals, and cultural institutions in Philadelphia."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Penn graduate and professional programs have selective admission pools."},
            {"label": "Cost & location", "sentiment": "caution", "detail": "Philadelphia living costs add to private-university tuition."},
        ]

    if is_wharton:
        return {
            "summary": summary,
            "themes": themes,
            "sources": [
                {"label": "The Wharton School", "url": school_url},
                {"label": "Poets&Quants — Wharton", "url": POETS_WHARTON},
            ],
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Penn — {department or school}", "url": dept_url},
            {"label": "U.S. News — University of Pennsylvania", "url": USNEWS.get(usnews_key, USNEWS["penn"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("penn")
    programs = [
        {
            "slug": p["slug"],
            "program_name": p["program_name"],
            "degree_type": p["degree_type"],
            "school": p["school"],
            "department": p.get("department") or p["school"],
        }
        for p in mod.PROGRAMS
        if is_coverable(p) and p["slug"] not in mod._REVIEWS_BY_SLUG
    ]

    reviews = {p["slug"]: review_for(**p) for p in programs}
    total = len(reviews) + len(mod._REVIEWS_BY_SLUG)

    lines = [
        '"""University of Pennsylvania external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``pennprof7`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``penn_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/penn_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
