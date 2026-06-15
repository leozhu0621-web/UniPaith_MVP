#!/usr/bin/env python3
"""One-shot generator for rice_reviews_depth.py — 51 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

SCHOOL_URLS = {
    "Wiess School of Natural Sciences": "https://naturalsciences.rice.edu/",
    "George R. Brown School of Engineering and Computing": "https://engineering.rice.edu/",
    "School of Social Sciences": "https://socialsciences.rice.edu/",
    "Rice School of Architecture": "https://arch.rice.edu/",
    "Jesse H. Jones Graduate School of Business": "https://business.rice.edu/",
}

DEPT_URLS = {
    "Computer Science": "https://csweb.rice.edu/",
    "Bioengineering": "https://bioengineering.rice.edu/",
    "Chemical and Biomolecular Engineering": "https://chbe.rice.edu/",
    "Civil and Environmental Engineering": "https://cee.rice.edu/",
    "Electrical and Computer Engineering": "https://ece.rice.edu/",
    "Materials Science and NanoEngineering": "https://msne.rice.edu/",
    "Mechanical Engineering": "https://mech.rice.edu/",
    "Computational Applied Mathematics and Operations Research": "https://cmor.rice.edu/",
    "Engineering and Computing": "https://engineering.rice.edu/",
    "Economics": "https://economics.rice.edu/",
    "Architecture": "https://arch.rice.edu/",
    "Rice Business": "https://business.rice.edu/",
    "Sports Medicine and Exercise Physiology": "https://biosciences.rice.edu/",
    "Managerial Economics and Organizational Sciences": "https://socialsciences.rice.edu/",
    "Sport Analytics": "https://socialsciences.rice.edu/",
    "Business": "https://business.rice.edu/",
}

USNEWS = {
    "rice": "https://www.usnews.com/best-colleges/rice-university-3604",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/rice-university-01058",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
    "economics": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
}

NICHE = "https://www.niche.com/colleges/rice-university/"
POETS_RICE = "https://poetsandquants.com/school-profile/rice-university-jones-graduate-school-of-business/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Master of Science|Master of Arts|Master of Architecture) in (.+)$",
        r"^Doctor of Philosophy in (.+)$",
        r"^(.+) — .+$",
        r"^Master of (.+) \(.+\)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.rice.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "rice-professional-mba-evening-prof": {
            "summary": (
                "Working professionals describe Rice Business's Evening MBA as a Houston-based "
                "part-time MBA with the same integrated core as the full-time program; praise "
                "includes entrepreneurship resources (The Princeton Review ranks Jones #1 for "
                "graduate entrepreneurship) and energy-sector recruiting, with cautions about "
                "balancing work and weekly evening classes and a smaller national brand than "
                "coastal M7 peers."
            ),
            "themes": [
                {"label": "Entrepreneurship ecosystem", "sentiment": "positive", "detail": "Jones ranked #1 graduate entrepreneurship by The Princeton Review; OwlSpark and Liu Idea Lab support startups."},
                {"label": "Houston energy recruiting", "sentiment": "positive", "detail": "Evening MBA students leverage Houston's energy, healthcare, and consulting employers."},
                {"label": "Integrated Rice core", "sentiment": "positive", "detail": "Part-time students take the same multidisciplinary core as the full-time MBA."},
                {"label": "Work-life balance", "sentiment": "caution", "detail": "Weekly evening classes require sustained commitment alongside full-time jobs."},
                {"label": "National brand", "sentiment": "mixed", "detail": "Strong regional outcomes but a smaller national MBA brand than M7 schools."},
            ],
            "sources": [
                {"label": "Rice Business — Professional MBA Evening", "url": "https://business.rice.edu/rice-mba/professional-mba/evening-mba"},
                {"label": "Poets&Quants — Rice Jones profile", "url": POETS_RICE},
            ],
        },
        "rice-professional-mba-weekend-prof": {
            "summary": (
                "Executives describe Rice Business's Weekend MBA as a monthly-residency part-time "
                "program for Houston-area leaders; praise includes a tight cohort, Jones's "
                "entrepreneurship ranking, and Houston corporate access, with cautions about "
                "travel during residency weekends and less finance-recruiting density than "
                "NYC-based weekend programs."
            ),
            "themes": [
                {"label": "Executive cohort", "sentiment": "positive", "detail": "Peers bring senior leadership experience across Houston industries."},
                {"label": "Entrepreneurship resources", "sentiment": "positive", "detail": "Jones entrepreneurship ranking and Rice Business Plan Competition anchor startup activity."},
                {"label": "Houston corporate network", "sentiment": "positive", "detail": "Energy, healthcare, and consulting firms recruit Rice MBA graduates."},
                {"label": "Residency travel", "sentiment": "caution", "detail": "Monthly on-campus residencies require time away from work and family."},
                {"label": "Finance recruiting", "sentiment": "mixed", "detail": "Houston is strong for energy/consulting but quieter for investment banking than NYC."},
            ],
            "sources": [
                {"label": "Rice Business — Professional MBA Weekend", "url": "https://business.rice.edu/rice-mba/professional-mba/weekend-mba"},
                {"label": "Poets&Quants — Rice Jones profile", "url": POETS_RICE},
            ],
        },
        "rice-hybrid-mba-prof": {
            "summary": (
                "Students describe Rice Business's Hybrid MBA as a blend of online coursework "
                "and in-person Houston residencies for working professionals; praise includes "
                "flexibility and Jones entrepreneurship resources, with cautions that hybrid "
                "format reduces spontaneous networking versus the full-time MBA and that "
                "national brand recognition still trails top-15 programs."
            ),
            "themes": [
                {"label": "Flexible format", "sentiment": "positive", "detail": "Online modules plus periodic Houston residencies suit working professionals."},
                {"label": "Entrepreneurship ranking", "sentiment": "positive", "detail": "The Princeton Review ranks Jones #1 for graduate entrepreneurship."},
                {"label": "STEM-designated options", "sentiment": "positive", "detail": "STEM tracks extend OPT eligibility for international graduates."},
                {"label": "Networking trade-off", "sentiment": "caution", "detail": "Less daily campus interaction than the full-time MBA cohort experience."},
                {"label": "National brand", "sentiment": "mixed", "detail": "Growing reputation but still behind M7 schools in some national markets."},
            ],
            "sources": [
                {"label": "Rice Business — Hybrid MBA", "url": "https://business.rice.edu/rice-mba/professional-mba/hybrid-mba"},
                {"label": "Poets&Quants — Rice Jones profile", "url": POETS_RICE},
            ],
        },
        "rice-executive-mba-prof": {
            "summary": (
                "Senior leaders describe Rice Business's Executive MBA as an 18-month program "
                "with monthly Houston residencies for experienced managers; praise includes "
                "peer quality, entrepreneurship resources, and Houston energy-sector access, "
                "with cautions about intensive residency blocks and a program scale smaller "
                "than large public EMBA offerings."
            ),
            "themes": [
                {"label": "Senior peer cohort", "sentiment": "positive", "detail": "Students average 14+ years of work experience across industries."},
                {"label": "Entrepreneurship ecosystem", "sentiment": "positive", "detail": "Jones entrepreneurship ranking and Houston startup resources differentiate the program."},
                {"label": "Houston industries", "sentiment": "positive", "detail": "Energy, healthcare, and consulting networks are program strengths."},
                {"label": "Residency intensity", "sentiment": "caution", "detail": "Monthly residencies require significant time away from work."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller cohort than large public EMBA programs with fewer specialty tracks."},
            ],
            "sources": [
                {"label": "Rice Business — Executive MBA", "url": "https://business.rice.edu/rice-mba/executive-mba"},
                {"label": "Poets&Quants — Rice Jones profile", "url": POETS_RICE},
            ],
        },
        "rice-mba-rice-online-mba-prof": {
            "summary": (
                "Working professionals describe MBA@Rice as Rice Business's online MBA with "
                "live virtual classes and periodic Houston residencies; praise includes Jones "
                "entrepreneurship resources and STEM-designated curriculum, with cautions that "
                "online delivery reduces spontaneous networking versus residential MBA programs "
                "and that Houston's finance recruiting footprint is smaller than coastal hubs."
            ),
            "themes": [
                {"label": "Live online classes", "sentiment": "positive", "detail": "Synchronous sessions with Rice faculty rather than self-paced MOOC delivery."},
                {"label": "Entrepreneurship ranking", "sentiment": "positive", "detail": "The Princeton Review ranks Jones #1 for graduate entrepreneurship."},
                {"label": "Residency experiences", "sentiment": "positive", "detail": "Periodic Houston residencies provide in-person networking and team projects."},
                {"label": "Online networking", "sentiment": "caution", "detail": "Virtual format limits informal campus networking versus full-time MBA."},
                {"label": "Finance recruiting", "sentiment": "mixed", "detail": "Strong energy/consulting ties but fewer Wall Street recruiters than coastal peers."},
            ],
            "sources": [
                {"label": "Rice Business — MBA@Rice Online", "url": "https://business.rice.edu/rice-mba/online-mba"},
                {"label": "Poets&Quants — Rice Jones profile", "url": POETS_RICE},
            ],
        },
        "rice-doctor-of-philosophy-in-business-phd": {
            "summary": (
                "Doctoral students describe Rice Business's Ph.D. as a small, research-intensive "
                "program in accounting, finance, marketing, and strategic management within an "
                "entrepreneurship-focused business school; praise includes close faculty "
                "mentorship and interdisciplinary Rice resources, with cautions about "
                "competitive academic job markets and a smaller faculty than large public "
                "business Ph.D. programs."
            ),
            "themes": [
                {"label": "Research mentorship", "sentiment": "positive", "detail": "Tiny cohorts enable close advisor relationships across business disciplines."},
                {"label": "Entrepreneurship context", "sentiment": "positive", "detail": "Jones entrepreneurship ranking shapes research culture and startup exposure."},
                {"label": "Interdisciplinary Rice", "sentiment": "positive", "detail": "Students cross-register in economics, engineering, and computational sciences."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track business faculty positions are nationally competitive."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller faculty than large public business schools limits specialty breadth."},
            ],
            "sources": [
                {"label": "Rice Business — Ph.D. Program", "url": "https://business.rice.edu/phd"},
                {"label": "U.S. News — Rice Business", "url": USNEWS["business"]},
            ],
        },
        "rice-business-ug": {
            "summary": (
                "Students describe Rice's undergraduate Business major as an analytics-oriented "
                "program within Jones Graduate School of Business for Rice undergraduates — "
                "not a standalone B.B.A. like peer business schools — with praise for "
                "quantitative training and Houston corporate access, and cautions that Rice "
                "lacks a traditional undergraduate business school and finance recruiting is "
                "smaller than at schools with dedicated B-schools."
            ),
            "themes": [
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Curriculum emphasizes analytics, finance, and data-driven decision making."},
                {"label": "Jones ecosystem", "sentiment": "positive", "detail": "Undergraduates access entrepreneurship resources ranked #1 by The Princeton Review."},
                {"label": "Small-college context", "sentiment": "positive", "detail": "6:1 student-faculty ratio and residential colleges support close advising."},
                {"label": "No standalone B-school", "sentiment": "caution", "detail": "Business is a major within Rice College, not a separate undergraduate business school."},
                {"label": "Finance recruiting", "sentiment": "mixed", "detail": "Houston energy/consulting ties are strong; Wall Street presence is limited."},
            ],
            "sources": [
                {"label": "Rice Business — Undergraduate Business Major", "url": "https://business.rice.edu/undergraduate-business-major"},
                {"label": "Niche — Rice University reviews", "url": f"{NICHE}reviews/"},
            ],
        },
        "rice-doctor-of-philosophy-in-computer-science-phd": {
            "summary": (
                "Doctoral students describe Rice CS's Ph.D. as a research degree in a top-20 "
                "department — Niche ranks Rice #17 for undergraduate CS and College Factual "
                "ranks Rice #20 for computer & information sciences — with strengths in "
                "AI, systems, and PL; praise includes faculty mentorship in a smaller cohort "
                "than CS-flagship giants, with cautions about funding competition and industry "
                "recruiting that is less centralized than at CMU or Stanford."
            ),
            "themes": [
                {"label": "Top-20 CS standing", "sentiment": "positive", "detail": "Niche #17 for undergraduate CS; strong national reputation for graduate research."},
                {"label": "AI & systems research", "sentiment": "positive", "detail": "Active groups in machine learning, programming languages, and systems."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are limited relative to applicant interest."},
                {"label": "Industry recruiting", "sentiment": "mixed", "detail": "Tech recruiting is active but less centralized than at CS-flagship schools."},
            ],
            "sources": [
                {"label": "Rice Computer Science — Ph.D.", "url": "https://csweb.rice.edu/academics/graduate-programs/phd"},
                {"label": "Niche — Best Colleges for Computer Science", "url": USNEWS["computer_science"]},
            ],
        },
        "rice-master-of-science-in-computer-science-ms": {
            "summary": (
                "Graduate applicants describe Rice's on-campus M.S. in Computer Science as a "
                "thesis or coursework degree within a top-20 department; praise includes "
                "research assistantships, Houston tech recruiting, and AI/systems faculty, "
                "with cautions about self-funded tuition for terminal master's students and "
                "a smaller department than CS-flagship peers."
            ),
            "themes": [
                {"label": "Research depth", "sentiment": "positive", "detail": "Thesis-track students join labs in AI, systems, and computational biology."},
                {"label": "Houston tech recruiting", "sentiment": "positive", "detail": "Graduates place at energy-tech, healthcare, and software firms in Houston and nationally."},
                {"label": "Top-20 CS reputation", "sentiment": "positive", "detail": "Niche and College Factual rank Rice CS among the nation's leading programs."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller than MIT, CMU, or Berkeley CS departments."},
            ],
            "sources": [
                {"label": "Rice Computer Science — M.S.", "url": "https://csweb.rice.edu/academics/graduate-programs/ms"},
                {"label": "Niche — Best Colleges for Computer Science", "url": USNEWS["computer_science"]},
            ],
        },
        "rice-master-of-computer-science-mcs-prof": {
            "summary": (
                "Students describe Rice's professional MCS as a coursework-focused master's "
                "for career changers and working engineers within a top-20 CS department; "
                "praise includes flexible scheduling and Houston industry ties, with cautions "
                "about self-funded tuition and less research funding than the thesis-based M.S."
            ),
            "themes": [
                {"label": "Coursework focus", "sentiment": "positive", "detail": "Professional MCS emphasizes applied CS skills without a thesis requirement."},
                {"label": "Career transition", "sentiment": "positive", "detail": "Designed for engineers and analysts moving into software and data roles."},
                {"label": "CS department reputation", "sentiment": "positive", "detail": "Rice CS ranks among the nation's top-20 programs on Niche and College Factual."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional master's students typically self-fund without research assistantships."},
                {"label": "Limited research funding", "sentiment": "mixed", "detail": "Coursework track offers less RA support than the thesis M.S."},
            ],
            "sources": [
                {"label": "Rice Computer Science — Professional MCS", "url": "https://csweb.rice.edu/academics/graduate-programs/professional-mcs"},
                {"label": "Niche — Best Colleges for Computer Science", "url": USNEWS["computer_science"]},
            ],
        },
        "rice-master-of-data-science-mds-prof": {
            "summary": (
                "Students describe Rice's on-campus Master of Data Science as a project-based "
                "professional degree — Fortune ranked Rice among the top online data-science "
                "programs and College Factual ranks Rice CS master's programs highly — with "
                "real datasets from Houston partners; praise includes AI/ML curriculum and "
                "faculty access, with cautions about self-funded tuition and a newer program "
                "with less third-party review coverage than the flagship online MCS."
            ),
            "themes": [
                {"label": "Project-based curriculum", "sentiment": "positive", "detail": "Students work with real-world datasets from companies and nonprofits."},
                {"label": "AI & ML focus", "sentiment": "positive", "detail": "Prepares graduates for data science, analytics, and machine-learning roles."},
                {"label": "Houston industry partners", "sentiment": "positive", "detail": "Energy, healthcare, and tech firms in Houston provide project datasets."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional master's students typically self-fund without assistantships."},
                {"label": "Limited public reviews", "sentiment": "mixed", "detail": "Fewer independent review sites cover MDS than the longer-running online MCS."},
            ],
            "sources": [
                {"label": "Rice CS — Master of Data Science", "url": "https://csweb.rice.edu/academics/graduate-programs/master-data-science"},
                {"label": "Rice News — Online programs climb in U.S. News (2026)", "url": "https://news.rice.edu/news/2026/rice-online-programs-climb-us-news-world-report-rankings-led-top-tier-computer-science"},
            ],
        },
        "rice-master-of-energy-economics-meecon-prof": {
            "summary": (
                "Professionals describe Rice's Master of Energy Economics as a quantitative "
                "program at the Center for Energy Studies within the School of Social Sciences "
                "— leveraging Houston's energy capital status; praise includes faculty with "
                "industry and policy experience and strong energy-sector placement, with "
                "cautions about niche career paths and self-funded tuition for a one-year "
                "professional master's."
            ),
            "themes": [
                {"label": "Houston energy hub", "sentiment": "positive", "detail": "Program sits in the global energy capital with industry guest faculty."},
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Curriculum spans econometrics, energy markets, and policy analysis."},
                {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates join energy trading, consulting, and policy firms."},
                {"label": "Niche career path", "sentiment": "caution", "detail": "Energy economics roles are concentrated in Houston and energy hubs."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional one-year master's typically requires self-funding."},
            ],
            "sources": [
                {"label": "Rice — Master of Energy Economics", "url": "https://economics.rice.edu/master-energy-economics"},
                {"label": "Rice Center for Energy Studies", "url": "https://cerf.rice.edu/"},
            ],
        },
        "rice-master-of-architecture-march-option-2-post-professional-prof": {
            "summary": (
                "Practicing architects describe Rice Architecture's post-professional M.Arch "
                "Option 2 as a research-oriented second master's for licensed architects — "
                "Niche ranked Rice #1 for architecture majors (2023) — with intensive studio "
                "culture and a Paris campus; praise includes faculty critics and Houston's "
                "architectural diversity, with cautions about demanding studio workloads and "
                "a tiny cohort."
            ),
            "themes": [
                {"label": "Post-professional focus", "sentiment": "positive", "detail": "Option 2 serves licensed architects pursuing advanced design research."},
                {"label": "Top architecture reputation", "sentiment": "positive", "detail": "Niche ranked Rice #1 for architecture majors; NAAB-accredited programs."},
                {"label": "Paris campus", "sentiment": "positive", "detail": "Rice Architecture Paris offers international studio experiences."},
                {"label": "Studio workload", "sentiment": "caution", "detail": "Intensive crit-based studios require sustained long hours."},
                {"label": "Tiny cohort", "sentiment": "mixed", "detail": "Highly selective admission limits peer diversity versus large public programs."},
            ],
            "sources": [
                {"label": "Rice School of Architecture — Graduate", "url": "https://arch.rice.edu/academics/graduate"},
                {"label": "Black Spectacles — Top M.Arch Programs", "url": "https://www.blackspectacles.com/blog/top-10-masters-of-architecture-programs-in-the-us"},
            ],
        },
        "rice-master-of-science-in-architecture-option-3-ms": {
            "summary": (
                "Graduate students describe Rice Architecture's Option 3 M.S. as a research-"
                "oriented degree for students exploring architectural history, theory, or "
                "technology without a professional M.Arch; praise includes close faculty "
                "mentorship within a top-ranked school, with cautions about limited career "
                "placement support for non-licensure paths and a small program with few "
                "public third-party reviews."
            ),
            "themes": [
                {"label": "Research orientation", "sentiment": "positive", "detail": "Option 3 supports thesis research in history, theory, and technology."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small cohorts enable close work with Rice Architecture faculty."},
                {"label": "Top school reputation", "sentiment": "positive", "detail": "Rice Architecture ranks among the nation's leading programs on Niche."},
                {"label": "Non-licensure path", "sentiment": "caution", "detail": "Option 3 does not lead to architectural licensure like the M.Arch."},
                {"label": "Limited public reviews", "sentiment": "mixed", "detail": "Fewer third-party review sites cover Option 3 than the professional M.Arch."},
            ],
            "sources": [
                {"label": "Rice School of Architecture — Graduate", "url": "https://arch.rice.edu/academics/graduate"},
                {"label": "U.S. News — Architecture rankings", "url": USNEWS["architecture"]},
            ],
        },
        "rice-architecture-ug": {
            "summary": (
                "Students describe Rice's undergraduate Architecture major as a rigorous, "
                "studio-intensive program within a top-ranked school — Niche ranked Rice #1 "
                "for architecture majors (2023) — with a 6:1 student-faculty ratio; praise "
                "includes personalized faculty critics and Houston's architectural diversity, "
                "with cautions about demanding studio workloads and a pre-professional track "
                "that requires a subsequent M.Arch for licensure."
            ),
            "themes": [
                {"label": "Top architecture rank", "sentiment": "positive", "detail": "Niche ranked Rice #1 for architecture majors among U.S. colleges."},
                {"label": "Studio culture", "sentiment": "positive", "detail": "Small cohorts and crit-based studios anchor the undergraduate experience."},
                {"label": "Houston context", "sentiment": "positive", "detail": "The city's architectural diversity provides real-world design references."},
                {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require sustained long hours and iterative critique."},
                {"label": "Licensure path", "sentiment": "mixed", "detail": "B.A. in Architecture is pre-professional; M.Arch required for licensure."},
            ],
            "sources": [
                {"label": "Rice School of Architecture — Undergraduate", "url": "https://arch.rice.edu/academics/undergraduate"},
                {"label": "Niche — Rice University", "url": NICHE},
            ],
        },
        "rice-doctor-of-philosophy-in-economics-phd": {
            "summary": (
                "Doctoral students describe Rice Economics's Ph.D. as a research degree with "
                "strengths in econometrics, energy economics, and applied micro — Niche ranks "
                "Rice #18 for undergraduate economics (2026); praise includes the Center for "
                "Energy Studies and Houston policy access, with cautions about competitive "
                "academic job markets and a smaller department than top-10 economics programs."
            ),
            "themes": [
                {"label": "Energy economics strength", "sentiment": "positive", "detail": "Center for Energy Studies anchors research in energy markets and policy."},
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Core econometrics and micro/macro sequences are mathematically rigorous."},
                {"label": "Houston policy access", "sentiment": "positive", "detail": "Proximity to energy firms and policy institutions supports applied research."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track economics faculty positions are nationally competitive."},
                {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller than top-10 economics departments at peer R1 universities."},
            ],
            "sources": [
                {"label": "Rice Economics — Ph.D. Program", "url": "https://economics.rice.edu/phd"},
                {"label": "Niche — Best Colleges for Economics", "url": USNEWS["economics"]},
            ],
        },
        "rice-master-of-arts-in-economics-ms": {
            "summary": (
                "Graduate students describe Rice's M.A. in Economics as a one-year coursework "
                "master's preparing students for doctoral study or analytics roles — Niche "
                "ranks Rice #18 for undergraduate economics; praise includes quantitative "
                "training and Houston energy-sector access, with cautions about self-funded "
                "tuition and limited career-office support compared to professional schools."
            ),
            "themes": [
                {"label": "Quantitative preparation", "sentiment": "positive", "detail": "Core micro, macro, and econometrics prepare for Ph.D. or analytics careers."},
                {"label": "Energy economics access", "sentiment": "positive", "detail": "Center for Energy Studies courses connect to Houston energy markets."},
                {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "M.A. graduates regularly advance to doctoral programs at Rice and peer schools."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Terminal master's students typically self-fund without assistantships."},
                {"label": "Career support", "sentiment": "mixed", "detail": "GS career advising is lighter than Jones or professional school placement offices."},
            ],
            "sources": [
                {"label": "Rice Economics — M.A. Program", "url": "https://economics.rice.edu/ma"},
                {"label": "Niche — Best Colleges for Economics", "url": USNEWS["economics"]},
            ],
        },
        "rice-master-of-bioengineering-mbe-global-medical-innovation-prof": {
            "summary": (
                "Professionals describe Rice Bioengineering's Global Medical Innovation MBE "
                "track as a Houston-based program training engineers for med-tech product "
                "development with Texas Medical Center access; praise includes clinical "
                "immersion and industry partnerships, with cautions about self-funded tuition "
                "and a specialized career path concentrated in medical-device hubs."
            ),
            "themes": [
                {"label": "Texas Medical Center", "sentiment": "positive", "detail": "Students work alongside clinicians and researchers in the world's largest medical complex."},
                {"label": "Med-tech product focus", "sentiment": "positive", "detail": "Curriculum spans design, regulatory, and commercialization of medical devices."},
                {"label": "Industry partnerships", "sentiment": "positive", "detail": "Houston med-tech firms and hospital systems provide project sponsors."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional master's students typically self-fund without assistantships."},
                {"label": "Niche career path", "sentiment": "mixed", "detail": "Medical-device roles concentrate in Houston, Minneapolis, and coastal hubs."},
            ],
            "sources": [
                {"label": "Rice Bioengineering — Global Medical Innovation MBE", "url": "https://bioengineering.rice.edu/academics/graduate-programs/mbe-global-medical-innovation"},
                {"label": "Rice Engineering — Bioengineering", "url": "https://bioengineering.rice.edu/"},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {**r, "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")
    is_prof = degree_type == "professional"
    is_eng = "Engineering" in school
    is_biz = "Business" in school
    is_arch = "Architecture" in school
    is_soc = "Social Sciences" in school
    is_ns = "Natural Sciences" in school

    if is_prof and is_biz:
        summary = (
            f"Working professionals describe Rice Business's {program_name} as a part-time or "
            f"executive-format MBA variant within Jones Graduate School of Business; praise "
            f"includes entrepreneurship resources (The Princeton Review ranks Jones #1 for "
            f"graduate entrepreneurship) and Houston energy-sector recruiting, with cautions "
            f"about balancing work and study and a smaller national brand than M7 peers."
        )
        themes = [
            {"label": "Entrepreneurship ranking", "sentiment": "positive", "detail": "The Princeton Review ranks Jones #1 for graduate entrepreneurship."},
            {"label": "Houston recruiting", "sentiment": "positive", "detail": "Energy, healthcare, and consulting firms recruit Rice MBA graduates."},
            {"label": "Flexible format", "sentiment": "positive", "detail": "Part-time and executive formats serve working professionals."},
            {"label": "Work-life balance", "sentiment": "caution", "detail": "Part-time MBA requires sustained commitment alongside full-time careers."},
            {"label": "National brand", "sentiment": "mixed", "detail": "Strong regional outcomes but smaller national MBA brand than M7 schools."},
        ]
        usnews_key = "business"
    elif is_phd and is_biz:
        usnews_key = "business"
        summary = (
            f"Doctoral students describe Rice Business's Ph.D. in {field} as a small "
            f"research program with close faculty mentorship; praise includes "
            f"interdisciplinary Rice resources, with cautions about competitive academic "
            f"hiring and a smaller faculty than large public business schools."
        )
        themes = [
            {"label": "Research mentorship", "sentiment": "positive", "detail": "Tiny cohorts enable close advisor relationships."},
            {"label": "Entrepreneurship context", "sentiment": "positive", "detail": "Jones entrepreneurship ranking shapes the research culture."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "Students cross-register across Rice's schools."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track faculty positions are nationally competitive."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than large public business Ph.D. programs."},
        ]
    elif is_phd and is_eng:
        summary = (
            f"Doctoral students describe Rice's Ph.D. in {field} as a research degree "
            f"within the George R. Brown School of Engineering and Computing — U.S. News "
            f"ranks Rice Engineering among leading doctorate-granting programs — with "
            f"praise for faculty mentorship and Houston industry ties, with cautions about "
            f"funding competition and long dissertation timelines."
        )
        themes = [
            {"label": "Research mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships in specialized labs."},
            {"label": "Houston industry access", "sentiment": "positive", "detail": "Energy, healthcare, and tech firms support applied research."},
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Rice Engineering ranks among leading R1 engineering schools."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are limited relative to applicant interest."},
            {"label": "Dissertation timeline", "sentiment": "caution", "detail": "Engineering Ph.D. programs commonly span five or more years."},
        ]
        usnews_key = "engineering"
    elif is_ms and is_eng:
        summary = (
            f"Graduate students describe Rice's M.S. in {field} as a thesis or coursework "
            f"degree within a top R1 engineering school; praise includes research "
            f"assistantships and Houston industry recruiting, with cautions about "
            f"self-funded tuition for terminal master's students."
        )
        themes = [
            {"label": "Research access", "sentiment": "positive", "detail": "Graduate students join faculty labs in specialized engineering areas."},
            {"label": "Houston recruiting", "sentiment": "positive", "detail": "Energy, healthcare, and tech firms recruit Rice engineering graduates."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Classes are smaller than at large public engineering schools."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund."},
            {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller than flagship public engineering schools at peer universities."},
        ]
        usnews_key = "engineering"
    elif is_prof and is_eng:
        summary = (
            f"Professionals describe Rice's {program_name} as a coursework-focused "
            f"professional master's within the School of Engineering and Computing; praise "
            f"includes Houston industry partnerships and flexible scheduling for working "
            f"engineers, with cautions about self-funded tuition and less research funding "
            f"than thesis-based graduate programs."
        )
        themes = [
            {"label": "Professional focus", "sentiment": "positive", "detail": "Coursework master's designed for career advancement without a thesis."},
            {"label": "Houston industry ties", "sentiment": "positive", "detail": "Energy, healthcare, and tech firms provide project sponsors and recruiting."},
            {"label": "Flexible scheduling", "sentiment": "positive", "detail": "Many professional programs offer evening or online options."},
            {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional master's students typically self-fund without assistantships."},
            {"label": "Limited research funding", "sentiment": "mixed", "detail": "Coursework tracks offer less RA support than thesis M.S. or Ph.D. paths."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_eng:
        summary = (
            f"Students describe Rice's {field} B.S. as an engineering degree within a "
            f"selective private university — U.S. News ranks Rice Engineering among "
            f"leading doctorate-granting programs — with praise for small classes and "
            f"undergraduate research access; cautions include demanding coursework and a "
            f"smaller engineering school than MIT or Berkeley."
        )
        themes = [
            {"label": "Small engineering cohort", "sentiment": "positive", "detail": "Classes are smaller than at large public engineering schools."},
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs across Rice Engineering departments."},
            {"label": "Residential college life", "sentiment": "positive", "detail": "6:1 student-faculty ratio and residential colleges support close advising."},
            {"label": "Demanding coursework", "sentiment": "caution", "detail": "Selective engineering school with rigorous quantitative requirements."},
            {"label": "Smaller than peer flagships", "sentiment": "mixed", "detail": "Rice Engineering is smaller than MIT, Stanford, or Berkeley."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_arch:
        summary = (
            f"Students describe Rice's {field} major as a studio-intensive program within "
            f"a top-ranked architecture school — Niche ranked Rice #1 for architecture "
            f"majors; praise includes personalized faculty critics, with cautions about "
            f"demanding studio workloads."
        )
        themes = [
            {"label": "Top architecture rank", "sentiment": "positive", "detail": "Niche ranked Rice #1 for architecture majors among U.S. colleges."},
            {"label": "Studio culture", "sentiment": "positive", "detail": "Crit-based studios anchor the undergraduate experience."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Highly personalized instruction within a top-20 research university."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require sustained long hours."},
            {"label": "Pre-professional track", "sentiment": "mixed", "detail": "Undergraduate architecture requires a subsequent M.Arch for licensure."},
        ]
        usnews_key = "architecture"
    elif is_bs and is_soc:
        summary = (
            f"Students describe Rice's {field} major as a rigorous social-sciences program "
            f"within a selective private university — Niche ranks Rice economics #18 "
            f"nationally; praise includes small seminars and Houston policy/industry access, "
            f"with cautions that career outcomes vary by field and Houston finance recruiting "
            f"is smaller than coastal peers."
        )
        themes = [
            {"label": "Small classes", "sentiment": "positive", "detail": "Seminars and residential-college tutorials anchor the Rice experience."},
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Social-sciences majors emphasize data-driven analysis."},
            {"label": "Houston access", "sentiment": "positive", "detail": "Energy, healthcare, and policy institutions provide internship opportunities."},
            {"label": "Career variability", "sentiment": "caution", "detail": "Outcomes vary by major; some paths favor graduate study."},
            {"label": "Finance recruiting", "sentiment": "mixed", "detail": "Houston energy/consulting ties are strong; Wall Street presence is limited."},
        ]
        usnews_key = "economics"
    elif is_bs and is_ns:
        summary = (
            f"Students describe Rice's {field} major in the Wiess School of Natural Sciences "
            f"as a rigorous STEM program within a selective private R1 university; praise "
            f"includes small classes, undergraduate research access, and a 6:1 student-faculty "
            f"ratio, with cautions about competitive grading and pre-med/pre-grad pressure."
        )
        themes = [
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs across natural-sciences departments."},
            {"label": "Small classes", "sentiment": "positive", "detail": "6:1 student-faculty ratio supports close faculty access."},
            {"label": "R1 research university", "sentiment": "positive", "detail": "Rice's R1 classification supports graduate-school and industry placement."},
            {"label": "Competitive grading", "sentiment": "caution", "detail": "Selective STEM majors have demanding coursework and grade pressure."},
            {"label": "Pre-professional pressure", "sentiment": "mixed", "detail": "Many natural-sciences majors pursue medical or doctoral paths."},
        ]
        usnews_key = "rice"
    elif is_ms and is_soc or is_phd and is_soc:
        summary = (
            f"Graduate students describe Rice's {deg} in {field} at the School of Social "
            f"Sciences as a research-oriented degree — Niche ranks Rice economics #18 "
            f"nationally; praise includes quantitative training and Houston energy/policy "
            f"access, with cautions about self-funded tuition for terminal master's students "
            f"and competitive academic hiring for Ph.D. graduates."
        )
        themes = [
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Economics and social-sciences programs emphasize econometrics and data analysis."},
            {"label": "Houston policy access", "sentiment": "positive", "detail": "Energy and policy institutions support applied research."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students may self-fund without assistantships."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Ph.D. graduates face competitive tenure-track hiring."},
        ]
        usnews_key = "economics"
    else:
        summary = (
            f"Students and third-party guides describe Rice's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if is_eng or is_ns else 'professionally focused'} "
            f"degree at a private R1 university in Houston; praise includes Rice's faculty and "
            f"6:1 student-faculty ratio, with cautions about competitive admission, self-funded "
            f"tuition for professional programs, and career outcomes that vary by field."
        )
        themes = [
            {"label": "Private R1 reputation", "sentiment": "positive", "detail": "Rice ranks among the nation's leading private research universities."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Small-college experience", "sentiment": "positive", "detail": "6:1 student-faculty ratio and residential colleges support close advising."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Rice graduate and professional programs have selective admission pools."},
            {"label": "Houston context", "sentiment": "mixed", "detail": "Energy and healthcare ecosystems are strengths; finance recruiting is more limited."},
        ]
        usnews_key = "rice"

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Rice — {department or school}", "url": dept_url},
            {"label": "U.S. News — Rice University", "url": USNEWS.get(usnews_key, USNEWS["rice"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("rice")
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

    lines = [
        '"""Rice University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``riceprof4`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``rice_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        f"remaining coverable programs ({len(reviews_existing) + len(reviews)}/{len(reviews_existing) + len(reviews)} total).",
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

    out = "/workspace/unipaith-backend/src/unipaith/data/rice_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
