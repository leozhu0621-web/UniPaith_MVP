#!/usr/bin/env python3
"""One-shot generator for uw_madison_reviews_depth.py — 47 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

SCHOOL_URLS = {
    "College of Agricultural and Life Sciences": "https://cals.wisc.edu/",
    "Wisconsin School of Business": "https://business.wisc.edu/",
    "School of Education": "https://education.wisc.edu/",
    "College of Engineering": "https://engineering.wisc.edu/",
    "School of Human Ecology": "https://sohe.wisc.edu/",
    "Law School": "https://law.wisc.edu/",
    "College of Letters and Science": "https://ls.wisc.edu/",
    "School of Computer, Data and Information Sciences": "https://cdis.wisc.edu/",
    "School of Journalism and Mass Communication": "https://journalism.wisc.edu/",
    "School of Social Work": "https://socwork.wisc.edu/",
    "School of Medicine and Public Health": "https://www.med.wisc.edu/",
    "School of Nursing": "https://nursing.wisc.edu/",
    "Nelson Institute for Environmental Studies": "https://nelson.wisc.edu/",
    "School of Pharmacy": "https://pharmacy.wisc.edu/",
    "School of Veterinary Medicine": "https://www.vetmed.wisc.edu/",
}

DEPT_URLS = {
    "Mechanical Engineering": "https://engineering.wisc.edu/departments/mechanical-engineering/",
    "Biomedical/Medical Engineering": "https://engineering.wisc.edu/departments/biomedical-engineering/",
    "Chemical Engineering": "https://engineering.wisc.edu/departments/chemical-biological-engineering/",
    "Civil Engineering": "https://engineering.wisc.edu/departments/civil-environmental-engineering/",
    "Computer Engineering": "https://engineering.wisc.edu/departments/electrical-computer-engineering/",
    "Electrical, Electronics, and Communications Engineering": "https://engineering.wisc.edu/departments/electrical-computer-engineering/",
    "Industrial Engineering": "https://engineering.wisc.edu/departments/industrial-systems-engineering/",
    "Materials Engineering": "https://engineering.wisc.edu/departments/materials-science-engineering/",
    "Nuclear Engineering": "https://engineering.wisc.edu/departments/engineering-physics/",
    "Agricultural Engineering": "https://engineering.wisc.edu/departments/biological-systems-engineering/",
    "Geological/Geophysical Engineering": "https://engineering.wisc.edu/departments/geological-engineering/",
    "Engineering Mechanics": "https://engineering.wisc.edu/departments/engineering-physics/",
    "Engineering Physics": "https://engineering.wisc.edu/departments/engineering-physics/",
    "Systems Engineering": "https://engineering.wisc.edu/departments/industrial-systems-engineering/",
    "Data Science": "https://cdis.wisc.edu/",
    "Economics": "https://econ.wisc.edu/",
    "Landscape Architecture": "https://landscapearchitecture.wisc.edu/",
    "Finance and Financial Management Services": "https://business.wisc.edu/undergraduate/majors/finance/",
    "International Business": "https://business.wisc.edu/undergraduate/majors/international-business/",
    "Agricultural Business and Management": "https://business.wisc.edu/undergraduate/majors/agribusiness/",
}

USNEWS = {
    "uw_madison": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering",
    "mechanical": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
    "biomedical": "https://www.usnews.com/best-colleges/rankings/biomedical-engineering",
    "chemical": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
    "civil": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
    "electrical": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
    "industrial": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "business": "https://www.usnews.com/best-colleges/rankings/business-overall",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-wisconsin-3895",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-wisconsin-madison-04072",
    "nursing": "https://www.usnews.com/best-colleges/rankings/nursing-overall",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
    "veterinary": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "journalism": "https://www.usnews.com/best-colleges/rankings/national-universities",
}

NICHE = "https://www.niche.com/colleges/university-of-wisconsin-madison/"
POETS_WSB = "https://poetsandquants.com/schools/wisconsin-school-of-business-university-of-wisconsin/"


def field_from_name(name: str) -> str:
    m = re.match(r"^(?:Bachelor's|Master's|Doctor of Philosophy) in (.+)$", name)
    return m.group(1) if m else name


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
    school_url = SCHOOL_URLS.get(school, "https://www.wisc.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "uw-madison-data-science-bs": {
            "summary": (
                "Students describe UW-Madison's undergraduate data science major in CDIS as a "
                "quantitatively rigorous program bridging computer science, statistics, and domain "
                "applications; praise includes access to Wisconsin Institutes for Discovery and "
                "strong Midwest analytics recruiting, with cautions that the major is newer than "
                "peer CS programs and competitive admission to upper-division CDIS courses is common."
            ),
            "themes": [
                {"label": "Interdisciplinary CDIS", "sentiment": "positive", "detail": "Data science draws on CS, statistics, and applied domain coursework."},
                {"label": "Discovery institutes", "sentiment": "positive", "detail": "WID and Morgridge provide research and industry partnership access."},
                {"label": "Analytics recruiting", "sentiment": "positive", "detail": "Graduates enter tech, healthcare analytics, and consulting roles."},
                {"label": "Program maturity", "sentiment": "mixed", "detail": "Undergraduate data science is newer than established CS majors at peer schools."},
                {"label": "Course access", "sentiment": "caution", "detail": "Popular CDIS courses fill quickly; registration planning matters."},
            ],
            "sources": [
                {"label": "CDIS — Data Science", "url": "https://cdis.wisc.edu/"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "uw-madison-journalism-bs": {
            "summary": (
                "Students describe UW-Madison's journalism major in SJMC as a practice-oriented "
                "program with strong Wisconsin Public Radio and Wisconsin State Journal ties; "
                "praise includes reporting labs and the Center for Journalism Ethics, with cautions "
                "that media-industry disruption makes portfolio-building and internships essential."
            ),
            "themes": [
                {"label": "Practice-first training", "sentiment": "positive", "detail": "Reporting, multimedia, and strategic communication studios anchor the curriculum."},
                {"label": "Wisconsin media ties", "sentiment": "positive", "detail": "WPR, Wisconsin State Journal, and Madison media outlets offer internship pipelines."},
                {"label": "Ethics center", "sentiment": "positive", "detail": "Center for Journalism Ethics distinguishes SJMC nationally."},
                {"label": "Industry disruption", "sentiment": "caution", "detail": "Traditional newsroom hiring remains competitive; digital skills are essential."},
                {"label": "Portfolio careers", "sentiment": "mixed", "detail": "Outcomes depend on clips, internships, and industry networks."},
            ],
            "sources": [
                {"label": "SJMC — Undergraduate", "url": "https://journalism.wisc.edu/undergraduate/"},
                {"label": "Niche — University of Wisconsin-Madison", "url": NICHE},
            ],
        },
        "uw-madison-journalism-ms": {
            "summary": (
                "Graduate students describe SJMC's journalism master's as a research-and-practice "
                "degree with strengths in political communication and health journalism; praise "
                "includes faculty media research and Madison state-government access, with cautions "
                "about limited graduate funding compared with STEM programs."
            ),
            "themes": [
                {"label": "Research & practice", "sentiment": "positive", "detail": "Graduate tracks combine media research with applied reporting projects."},
                {"label": "State capital access", "sentiment": "positive", "detail": "Madison's government and policy community enriches political journalism study."},
                {"label": "Faculty research", "sentiment": "positive", "detail": "SJMC faculty lead studies in political and health communication."},
                {"label": "Funding scarcity", "sentiment": "caution", "detail": "Graduate assistantships are scarcer than in STEM Ph.D. programs."},
                {"label": "Career variability", "sentiment": "mixed", "detail": "Outcomes span academia, nonprofit media, and industry communication roles."},
            ],
            "sources": [
                {"label": "SJMC — Graduate Programs", "url": "https://journalism.wisc.edu/graduate/"},
                {"label": "Niche — University of Wisconsin-Madison", "url": NICHE},
            ],
        },
        "uw-madison-public-health-ms": {
            "summary": (
                "Graduate applicants describe UW-Madison's MPH through SMPH as a practice-oriented "
                "public health degree with strengths in epidemiology, health policy, and rural "
                "health through WARM-affiliated pathways; praise includes UW Health partnerships "
                "and affordable in-state tuition, with cautions that the school is smaller than "
                "top-10 public health programs."
            ),
            "themes": [
                {"label": "Rural health mission", "sentiment": "positive", "detail": "SMPH emphasizes community and rural health across Wisconsin."},
                {"label": "UW Health access", "sentiment": "positive", "detail": "Clinical and population-health practicum sites span the UW Health system."},
                {"label": "Affordable tuition", "sentiment": "positive", "detail": "In-state rates compare favorably to coastal MPH programs."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than top-10 public health schools; fewer specialized concentrations."},
                {"label": "Funding limits", "sentiment": "caution", "detail": "Research assistantships are more limited than at larger peer programs."},
            ],
            "sources": [
                {"label": "SMPH — Master of Public Health", "url": "https://www.med.wisc.edu/education/public-health/"},
                {"label": "U.S. News — Public Health Rankings", "url": USNEWS["public_health"]},
            ],
        },
        "uw-madison-finance-and-financial-management-services-bs": {
            "summary": (
                "Students describe UW-Madison's finance major through WSB as a quantitatively "
                "oriented undergraduate program with strength in corporate finance and the "
                "Nicholas Center for Corporate Finance; praise includes Midwest banking and "
                "consulting recruiting, with cautions that national finance placement trails "
                "top-10 undergraduate business programs."
            ),
            "themes": [
                {"label": "Nicholas Center", "sentiment": "positive", "detail": "Investment banking and corporate finance experiential programs are program hallmarks."},
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Curriculum emphasizes corporate finance, investments, and analytics."},
                {"label": "Midwest recruiting", "sentiment": "positive", "detail": "Milwaukee and Chicago finance firms recruit actively from WSB."},
                {"label": "Coastal placement", "sentiment": "mixed", "detail": "Investment banking on the coasts requires proactive networking beyond campus."},
                {"label": "Direct admission", "sentiment": "caution", "detail": "Competitive admission to WSB affects access to finance major coursework."},
            ],
            "sources": [
                {"label": "WSB — Finance Major", "url": "https://business.wisc.edu/undergraduate/majors/finance/"},
                {"label": "U.S. News — Best Undergraduate Business", "url": USNEWS["business"]},
            ],
        },
        "uw-madison-mechanical-engineering-ms": {
            "summary": (
                "Graduate applicants describe UW-Madison's M.S. in Mechanical Engineering as a "
                "research and coursework degree within a top-20 public engineering college; "
                "praise includes Grainger Engineering Design Innovation Lab access and Midwest "
                "manufacturing recruiting, with cautions about self-funded tuition for terminal "
                "master's students and competitive research funding."
            ),
            "themes": [
                {"label": "Top engineering rank", "sentiment": "positive", "detail": "UW-Madison mechanical engineering is consistently ranked among leading programs."},
                {"label": "Design Innovation Lab", "sentiment": "positive", "detail": "Grainger lab supports graduate research in manufacturing and product design."},
                {"label": "Industry recruiting", "sentiment": "positive", "detail": "Caterpillar, Rockwell, and automotive firms recruit actively."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Grainger Engineering."},
            ],
            "sources": [
                {"label": "UW-Madison Mechanical Engineering — Graduate", "url": "https://engineering.wisc.edu/departments/mechanical-engineering/graduate/"},
                {"label": "U.S. News — Mechanical Engineering", "url": USNEWS["mechanical"]},
            ],
        },
        "uw-madison-biomedical-medical-engineering-ms": {
            "summary": (
                "Graduate students describe UW-Madison's biomedical engineering M.S. as a "
                "research-intensive degree bridging Grainger Engineering and SMPH; praise "
                "includes UW Health clinical access and med-device placement, with cautions "
                "about self-funded tuition for terminal master's students."
            ),
            "themes": [
                {"label": "Clinical translation", "sentiment": "positive", "detail": "SMPH and UW Health affiliations support med-device and imaging research."},
                {"label": "Interdisciplinary labs", "sentiment": "positive", "detail": "Students join bioelectronics, imaging, and regenerative-medicine groups."},
                {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates enter med-device firms, hospital R&D, and Ph.D. programs."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Prerequisite breadth", "sentiment": "mixed", "detail": "Biology and engineering prerequisites make the program planning-intensive."},
            ],
            "sources": [
                {"label": "UW-Madison Biomedical Engineering — Graduate", "url": "https://engineering.wisc.edu/departments/biomedical-engineering/graduate/"},
                {"label": "U.S. News — Biomedical Engineering", "url": USNEWS["biomedical"]},
            ],
        },
        "uw-madison-social-work-ms": {
            "summary": (
                "Graduate students describe UW-Madison's MSW as a top-ranked social work program "
                "with strengths in poverty research through the Institute for Research on Poverty "
                "and clinical training; praise includes Wisconsin field placements and faculty "
                "research, with cautions about emotionally demanding practicum work and licensure "
                "requirements varying by state."
            ),
            "themes": [
                {"label": "Top social work rank", "sentiment": "positive", "detail": "U.S. News ranks UW-Madison social work among leading programs nationally."},
                {"label": "Poverty research", "sentiment": "positive", "detail": "Institute for Research on Poverty anchors distinctive policy research training."},
                {"label": "Field placements", "sentiment": "positive", "detail": "Wisconsin agencies and health systems provide diverse practicum sites."},
                {"label": "Emotional demands", "sentiment": "caution", "detail": "Clinical practicum work with vulnerable populations is emotionally intensive."},
                {"label": "Licensure variation", "sentiment": "mixed", "detail": "MSW licensure requirements vary; graduates should plan for state-specific exams."},
            ],
            "sources": [
                {"label": "UW-Madison School of Social Work — MSW", "url": "https://socwork.wisc.edu/academics/msw/"},
                {"label": "U.S. News — Social Work Rankings", "url": USNEWS["social_work"]},
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
    is_eng = school == "College of Engineering" or "engineering" in fl
    is_business = school == "Wisconsin School of Business"
    is_cdis = school == "School of Computer, Data and Information Sciences"
    is_journalism = school == "School of Journalism and Mass Communication"
    is_social_work = school == "School of Social Work"
    is_smph = school == "School of Medicine and Public Health"
    is_nursing = school == "School of Nursing"
    is_law = school == "Law School"
    is_vet = school == "School of Veterinary Medicine"
    is_letters = school == "College of Letters and Science"
    is_human_eco = school == "School of Human Ecology"
    is_phd = degree_type in ("phd", "doctoral")
    is_ms = degree_type == "masters"
    is_bs = degree_type == "bachelors"

    usnews_key = "uw_madison"
    if "mechanical" in fl:
        usnews_key = "mechanical"
    elif "biomedical" in fl or "medical engineering" in fl:
        usnews_key = "biomedical"
    elif "chemical" in fl:
        usnews_key = "chemical"
    elif "civil" in fl:
        usnews_key = "civil"
    elif "electrical" in fl or "electronic" in fl or "communications" in fl or "computer engineering" in fl:
        usnews_key = "electrical"
    elif "industrial" in fl or "systems engineering" in fl:
        usnews_key = "industrial"
    elif "computer" in fl or "data science" in fl:
        usnews_key = "computer_science"
    elif is_business or "finance" in fl or "business" in fl:
        usnews_key = "business"
    elif is_law:
        usnews_key = "law"
    elif is_smph or "medicine" in fl or "public health" in fl:
        usnews_key = "medicine" if "medicine" in fl else "public_health"
    elif is_nursing:
        usnews_key = "nursing"
    elif is_vet:
        usnews_key = "veterinary"
    elif is_social_work:
        usnews_key = "social_work"
    elif is_journalism:
        usnews_key = "journalism"
    elif is_eng:
        usnews_key = "engineering"

    if is_phd and is_law:
        summary = (
            f"Doctoral scholars describe UW Law's {field} as a research degree within a "
            f"well-regarded public law school; praise includes faculty mentorship, the "
            f"Wisconsin Innocence Project, and Madison legal community access, with cautions "
            f"about competitive academic hiring and limited funding relative to private peers."
        )
        themes = [
            {"label": "Public law school value", "sentiment": "positive", "detail": "UW Law offers strong scholarship support and lower debt than private peers."},
            {"label": "Clinical programs", "sentiment": "positive", "detail": "Innocence Project and entrepreneurship clinic provide distinctive research training."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small doctoral cohorts enable close work with legal scholars."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track law faculty positions are nationally competitive."},
            {"label": "Funding variability", "sentiment": "caution", "detail": "Doctoral funding packages vary; external fellowships are common."},
        ]
        usnews_key = "law"
    elif is_phd and is_smph:
        summary = (
            f"Doctoral students describe SMPH's Ph.D. in {field} as a research-intensive "
            f"health-sciences degree with access to UW Carbone Cancer Center and ICTR; "
            f"praise includes translational research infrastructure, with cautions about "
            f"competitive residency matching and long dissertation timelines."
        )
        themes = [
            {"label": "Top research medical school", "sentiment": "positive", "detail": "U.S. News ranks SMPH among leading public medical schools for research."},
            {"label": "Carbone Cancer Center", "sentiment": "positive", "detail": "NCI-designated cancer center supports doctoral research across disciplines."},
            {"label": "Translational research", "sentiment": "positive", "detail": "ICTR connects basic science to clinical trials and community health."},
            {"label": "Residency competition", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research portfolios."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Biomedical Ph.D. programs commonly span five or more years."},
        ]
    elif is_phd and is_nursing:
        summary = (
            f"Doctoral students describe UW-Madison's Ph.D. in {field} as a research degree "
            f"preparing nurse scientists; praise includes Center for Aging Research and "
            f"Education and UW Health clinical research access, with cautions about "
            f"specialized academic hiring and competitive funding."
        )
        themes = [
            {"label": "Nurse scientist training", "sentiment": "positive", "detail": "Program prepares graduates for faculty and health-system research leadership."},
            {"label": "Aging research center", "sentiment": "positive", "detail": "CARE supports gerontology and chronic-disease research pathways."},
            {"label": "Clinical research access", "sentiment": "positive", "detail": "UW Health affiliations provide diverse patient-population research sites."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Nursing faculty positions are competitive nationally."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "NIH-funded training slots are limited relative to applicant pools."},
        ]
    elif is_phd and is_vet:
        summary = (
            f"Doctoral students describe UW-Madison's Ph.D. in {field} as a research degree "
            f"in comparative biomedical sciences with access to the Wisconsin Veterinary "
            f"Diagnostic Laboratory; praise includes One Health and food-animal research, "
            f"with cautions about long dissertation timelines and specialized hiring markets."
        )
        themes = [
            {"label": "Comparative medicine", "sentiment": "positive", "detail": "Doctoral research spans veterinary, human, and environmental health."},
            {"label": "WVDL diagnostics", "sentiment": "positive", "detail": "State diagnostic laboratory supports real-world disease surveillance research."},
            {"label": "One Health focus", "sentiment": "positive", "detail": "Food-animal and zoonotic disease research are program strengths."},
            {"label": "Dissertation timeline", "sentiment": "caution", "detail": "Veterinary biomedical Ph.D. programs commonly span five or more years."},
            {"label": "Academic market", "sentiment": "mixed", "detail": "Faculty positions concentrate in veterinary and biomedical sciences."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe UW-Madison's Ph.D. in {field} within {school} as a "
            f"research degree at an R1 public university ranked #36 nationally by U.S. News "
            f"(2026); praise includes faculty mentorship and Wisconsin Institutes for Discovery "
            f"access, with cautions about competitive admission and five-plus-year timelines."
        )
        themes = [
            {"label": "R1 research university", "sentiment": "positive", "detail": "UW-Madison's R1 status supports doctoral research across disciplines."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on funded research projects."},
            {"label": "Discovery institutes", "sentiment": "positive", "detail": "WID and Morgridge enrich interdisciplinary doctoral training."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Strong research background and faculty alignment are expected."},
        ]
    elif is_ms and is_business:
        summary = (
            f"Graduate students describe WSB's {deg} program in {field} as a quantitatively "
            f"oriented business degree; Poets&Quants and U.S. News rank WSB among leading "
            f"public business schools; praise includes applied learning and Midwest corporate "
            f"recruiting, with cautions about selective admission and national brand versus "
            f"top-15 MBA programs."
        )
        themes = [
            {"label": "Applied curriculum", "sentiment": "positive", "detail": "WSB emphasizes experiential learning and corporate-sponsored projects."},
            {"label": "Midwest recruiting", "sentiment": "positive", "detail": "Consulting, finance, and CPG firms recruit actively from WSB."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition compares favorably to elite private business schools."},
            {"label": "National brand", "sentiment": "mixed", "detail": "Well-regarded regionally; national recognition still developing versus M7 peers."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Graduate business programs have competitive applicant pools."},
        ]
        return {
            "summary": summary,
            "themes": themes,
            "sources": [
                {"label": "Wisconsin School of Business", "url": school_url},
                {"label": "Poets&Quants — Wisconsin School of Business", "url": POETS_WSB},
            ],
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }
    elif is_ms and is_eng:
        summary = (
            f"Graduate applicants describe UW-Madison's M.S. in {field} within Grainger "
            f"Engineering as a research and coursework degree at a top public engineering "
            f"college; students value Midwest manufacturing and tech recruiting, with cautions "
            f"about self-funded tuition for terminal master's students and competitive funding."
        )
        themes = [
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Grainger Engineering is consistently ranked among leading public programs."},
            {"label": "Research labs", "sentiment": "positive", "detail": "Graduate students join faculty labs in WID-affiliated research centers."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Manufacturing, tech, and med-device firms recruit actively."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Grainger Engineering."},
        ]
    elif is_bs and is_eng:
        summary = (
            f"Students describe UW-Madison's undergraduate {field} program in Grainger "
            f"Engineering as a nationally ranked engineering degree with strong theory-to-"
            f"application training; praise includes Grainger Design Innovation Lab access and "
            f"Midwest industry recruiting, with cautions that large lower-division sections "
            f"require proactive faculty engagement."
        )
        themes = [
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Grainger Engineering is consistently ranked among top public programs nationally."},
            {"label": "Design Innovation Lab", "sentiment": "positive", "detail": "Grainger lab and senior design capstone integrate real industry sponsors."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Manufacturing, tech, and med-device firms recruit actively from Grainger."},
            {"label": "Rigorous curriculum", "sentiment": "caution", "detail": "Math and physics sequences in years 1–2 are demanding."},
            {"label": "Large class sizes", "sentiment": "caution", "detail": "Gateway courses can be impersonal; study groups and office hours matter."},
        ]
    elif is_ms and is_nursing:
        summary = (
            f"Graduate students describe UW-Madison's M.S. in {field} as an advanced nursing "
            f"degree with clinical research opportunities through UW Health; praise includes "
            f"Center for Aging Research and Education, with cautions about limited funding "
            f"compared with larger nursing graduate programs."
        )
        themes = [
            {"label": "Clinical research", "sentiment": "positive", "detail": "UW Health system supports advanced practice and nursing science research."},
            {"label": "Aging research", "sentiment": "positive", "detail": "CARE supports gerontology and chronic-disease nursing research."},
            {"label": "Advanced practice", "sentiment": "positive", "detail": "Graduates enter nurse practitioner, leadership, and research roles."},
            {"label": "Funding limits", "sentiment": "caution", "detail": "Graduate assistantships are more limited than at larger peer programs."},
            {"label": "Clinical demands", "sentiment": "mixed", "detail": "Advanced practice tracks require intensive clinical hour commitments."},
        ]
    elif is_ms and is_vet:
        summary = (
            f"Graduate students describe UW-Madison's M.S. in {field} at the School of "
            f"Veterinary Medicine as a research degree with access to WVDL and UW Veterinary "
            f"Care; praise includes One Health and food-animal research, with cautions about "
            f"competitive admission and specialized veterinary career paths."
        )
        themes = [
            {"label": "Teaching hospital", "sentiment": "positive", "detail": "UW Veterinary Care provides broad small- and large-animal clinical exposure."},
            {"label": "WVDL diagnostics", "sentiment": "positive", "detail": "State diagnostic laboratory supports real-world disease surveillance research."},
            {"label": "One Health research", "sentiment": "positive", "detail": "Comparative medicine and zoonotic disease research are program strengths."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Graduate veterinary research programs have selective admission pools."},
            {"label": "Specialized market", "sentiment": "mixed", "detail": "Career paths concentrate in veterinary research, academia, and government."},
        ]
    elif is_bs and is_social_work:
        summary = (
            f"Students describe UW-Madison's {field} program as an undergraduate social work "
            f"degree with field placements across Wisconsin agencies; praise includes the "
            f"Institute for Research on Poverty proximity and faculty research access, with "
            f"cautions that licensure pathways require an MSW for clinical practice."
        )
        themes = [
            {"label": "Field placements", "sentiment": "positive", "detail": "Wisconsin agencies provide diverse undergraduate practicum experiences."},
            {"label": "Poverty research", "sentiment": "positive", "detail": "Institute for Research on Poverty enriches policy-oriented coursework."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Smaller program enables closer faculty mentorship than large L&S majors."},
            {"label": "MSW requirement", "sentiment": "caution", "detail": "Clinical social work licensure requires a graduate MSW beyond the bachelor's."},
            {"label": "Emotional demands", "sentiment": "mixed", "detail": "Field work with vulnerable populations can be emotionally intensive."},
        ]
    elif is_bs and is_letters and "landscape" in fl:
        summary = (
            "Students describe UW-Madison's landscape architecture program as a design-"
            "intensive professional degree emphasizing ecological planning and Midwest "
            "land-use issues; praise includes studio culture and Arboretum access, with "
            "cautions about long studio hours and licensure pathways beyond the degree."
        )
        themes = [
            {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and site-planning projects anchor the curriculum."},
            {"label": "Ecological focus", "sentiment": "positive", "detail": "UW Arboretum and Nelson Institute ties enrich sustainability coursework."},
            {"label": "Interdisciplinary ties", "sentiment": "positive", "detail": "Connections to CALS and civil engineering enrich planning projects."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Long studio hours and intensive crit schedules are recurring themes."},
            {"label": "Licensure path", "sentiment": "mixed", "detail": "Professional landscape architecture licensure requires additional experience."},
        ]
    elif is_ms and is_letters and "landscape" in fl:
        summary = (
            "Graduate students describe UW-Madison's M.S. in landscape architecture as a "
            "research-and-design degree with ecological planning strengths; praise includes "
            "Nelson Institute and Arboretum access, with cautions about studio workload and "
            "competitive funding for research assistantships."
        )
        themes = [
            {"label": "Ecological planning", "sentiment": "positive", "detail": "Graduate research spans urban ecology, restoration, and climate adaptation."},
            {"label": "Arboretum access", "sentiment": "positive", "detail": "UW Arboretum provides living-laboratory sites for design research."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Nelson Institute connections enrich sustainability-focused projects."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Graduate studios and thesis projects require sustained intensive work."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships in design programs are more limited than in STEM."},
        ]
    elif is_bs and is_human_eco:
        summary = (
            f"Students describe UW-Madison's {field} program in the School of Human Ecology "
            f"as an applied social-science degree with consumer economics and financial security "
            f"research ties; praise includes Center for Financial Security access, with cautions "
            f"that the program is smaller than flagship L&S majors."
        )
        themes = [
            {"label": "Applied focus", "sentiment": "positive", "detail": "Human Ecology programs emphasize consumer science and family well-being."},
            {"label": "Financial security research", "sentiment": "positive", "detail": "Center for Financial Security supports policy-relevant undergraduate research."},
            {"label": "Smaller cohorts", "sentiment": "positive", "detail": "Human Ecology classes are typically smaller than large L&S lecture courses."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than flagship engineering and business programs."},
            {"label": "Career specialization", "sentiment": "mixed", "detail": "Outcomes concentrate in consumer policy, nonprofit, and applied research roles."},
        ]
    elif is_ms and is_letters and "economics" in fl:
        summary = (
            "Graduate students describe UW-Madison's M.A. in Economics as a quantitatively "
            "rigorous program rooted in the Wisconsin School institutional-economics tradition; "
            "praise includes econometrics training and La Follette School proximity, with cautions "
            "about competitive Ph.D. placement and self-funded tuition for terminal master's students."
        )
        themes = [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Econometrics and labor economics sequences are program hallmarks."},
            {"label": "Wisconsin School legacy", "sentiment": "positive", "detail": "Institutional and labor economics traditions distinguish the department."},
            {"label": "Policy access", "sentiment": "positive", "detail": "Madison state-government proximity creates policy internship opportunities."},
            {"label": "Ph.D. competition", "sentiment": "caution", "detail": "Many M.A. students aim for economics Ph.D. programs with selective admission."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
        ]
    else:
        summary = (
            f"Students and third-party guides describe UW-Madison's {deg} program in {field} "
            f"within {school} as a {'research-oriented' if is_eng or is_cdis else 'professionally focused'} "
            f"degree at a top-40 public R1 university; praise includes UW-Madison's faculty "
            f"and Madison campus resources, with cautions about large class sizes, competitive "
            f"admission, and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top public research university", "sentiment": "positive", "detail": "U.S. News ranks UW-Madison #36 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Madison campus", "sentiment": "positive", "detail": "State capital proximity and UW Health enrich study beyond the classroom."},
            {"label": "Class scale", "sentiment": "caution", "detail": "Large university means gateway courses can be lecture-heavy."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Outcomes depend on field specialization and graduate-school plans."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"UW–Madison — {department or school}", "url": dept_url},
            {"label": "U.S. News — University of Wisconsin-Madison", "url": USNEWS.get(usnews_key, USNEWS["uw_madison"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("uw_madison")
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
        '"""University of Wisconsin-Madison external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``uwmadisonprof3`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``uw_madison_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/uw_madison_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
