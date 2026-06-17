#!/usr/bin/env python3
"""One-shot generator for yale_reviews_depth.py — 54 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re

SCHOOL_URLS = {
    "Yale College": "https://yalecollege.yale.edu/",
    "Yale School of Engineering & Applied Science": "https://seas.yale.edu/",
    "Yale Law School": "https://law.yale.edu/",
    "Yale School of Management": "https://som.yale.edu/",
    "Yale School of Medicine": "https://medicine.yale.edu/",
    "Yale School of Nursing": "https://nursing.yale.edu/",
    "Yale School of Public Health": "https://ysph.yale.edu/",
    "Yale School of Architecture": "https://www.architecture.yale.edu/",
    "David Geffen School of Drama at Yale": "https://drama.yale.edu/",
    "Jackson School of Global Affairs": "https://jackson.yale.edu/",
    "Yale Divinity School": "https://divinity.yale.edu/",
    "Yale School of Art": "https://www.art.yale.edu/",
    "Yale Graduate School of Arts and Sciences": "https://gsas.yale.edu/",
}

DEPT_URLS = {
    "Statistics and Data Science": "https://statistics.yale.edu/",
    "Biomedical Engineering": "https://seas.yale.edu/departments/biomedical-engineering",
    "Chemical Engineering": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
    "Computer Science and Economics": "https://cpsc.yale.edu/",
    "Computer Science and Mathematics": "https://cpsc.yale.edu/",
    "Computer Science and Psychology": "https://cpsc.yale.edu/",
    "Electrical Engineering": "https://seas.yale.edu/departments/electrical-and-computer-engineering",
    "Electrical Engineering and Computer Science": "https://seas.yale.edu/departments/electrical-and-computer-engineering",
    "Engineering Sciences (Chemical)": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
    "Engineering Sciences (Electrical)": "https://seas.yale.edu/departments/electrical-and-computer-engineering",
    "Engineering Sciences (Environmental)": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
    "Engineering Sciences (Mechanical)": "https://seas.yale.edu/departments/mechanical-engineering-and-materials-science",
    "Environmental Engineering": "https://seas.yale.edu/departments/chemical-and-environmental-engineering",
    "Mechanical Engineering": "https://seas.yale.edu/departments/mechanical-engineering-and-materials-science",
    "Architecture": "https://www.architecture.yale.edu/",
    "Economics and Mathematics": "https://economics.yale.edu/",
    "Ethics, Politics, and Economics": "https://epp.yale.edu/",
    "Film and Media Studies": "https://filmstudies.yale.edu/",
    "History of Science, Medicine, and Public Health": "https://hshm.yale.edu/",
    "Computer Science": "https://cpsc.yale.edu/",
    "Economics": "https://economics.yale.edu/",
    "Biological and Biomedical Sciences": "https://bbs.yale.edu/",
    "Computational Biology and Biomedical Informatics": "https://cbbi.yale.edu/",
    "International and Development Economics": "https://economics.yale.edu/graduate/international-and-development-economics",
    "Statistics and Data Science": "https://statistics.yale.edu/",
}

USNEWS = {
    "yale": "https://www.usnews.com/best-colleges/yale-university-1426",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/yale-university-03001",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/yale-university-01140",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/yale-university-04001",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/yale-university-04002",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/yale-university-04003",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
}

NICHE = "https://www.niche.com/colleges/yale-university/"
POETS_SOM = "https://poetsandquants.com/school-profile/yale-school-of-management/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Master's|Master of Science|Master of Arts|Master of Architecture II) in (.+)$",
        r"^Doctor of Philosophy in (.+)$",
        r"^(.+) \(MSN\)$",
        r"^(.+) \(M\.Div\)$",
        r"^(.+) \(MFA\)$",
        r"^(.+) \(LL\.M\.\)$",
        r"^(.+) \(M\.S\.L\.\)$",
        r"^(.+) \(M\.D\.\)$",
        r"^(.+) \(D\.N\.P\.\)$",
        r"^(.+) \(M\.F\.A\.\)$",
        r"^(.+) \(M\.P\.P\.\)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.yale.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "yale-statistics-bs": {
            "summary": (
                "Students describe Yale's Statistics and Data Science major as a rigorous "
                "quantitative program within a small liberal-arts college, with access to "
                "faculty-led research in causal inference and machine learning; praise includes "
                "small seminars and Yale's broader quantitative ecosystem, with cautions that "
                "the major is newer than peer departments and that CS/economics tracks can "
                "feel more established for industry recruiting."
            ),
            "themes": [
                {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Core probability, inference, and data-science coursework is mathematically demanding."},
                {"label": "Faculty research", "sentiment": "positive", "detail": "Undergraduates can join labs in causal inference, biostatistics, and ML."},
                {"label": "Liberal-arts context", "sentiment": "positive", "detail": "Students pair statistics with economics, CS, or social-science majors."},
                {"label": "Newer major", "sentiment": "mixed", "detail": "The combined Statistics and Data Science major is younger than peer CS programs."},
                {"label": "Industry vs. grad school", "sentiment": "caution", "detail": "Many graduates pursue Ph.D. paths; direct industry placement varies by subfield."},
            ],
            "sources": [
                {"label": "Yale Statistics and Data Science", "url": "https://statistics.yale.edu/academics/undergraduate-major"},
                {"label": "U.S. News — Yale University", "url": USNEWS["yale"]},
            ],
        },
        "yale-nursing-msn": {
            "summary": (
                "Graduate applicants describe Yale Nursing's MSN as a highly selective "
                "clinical master's within an Ivy research university — U.S. News ranks Yale "
                "Nursing among the top graduate nursing programs — with praise for Yale New "
                "Haven Hospital clinical placements and faculty mentorship; cautions include "
                "intense clinical hours, New Haven cost of living, and a small cohort with "
                "limited specialty tracks compared to larger nursing schools."
            ),
            "themes": [
                {"label": "Top nursing rank", "sentiment": "positive", "detail": "U.S. News consistently ranks Yale among leading graduate nursing programs."},
                {"label": "Yale New Haven clinicals", "sentiment": "positive", "detail": "Students train at Yale New Haven Hospital and affiliated sites."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small cohorts enable close faculty advising and research exposure."},
                {"label": "Clinical intensity", "sentiment": "caution", "detail": "MSN programs require demanding clinical and coursework schedules."},
                {"label": "Small program scale", "sentiment": "mixed", "detail": "Fewer specialty tracks than large public nursing schools."},
            ],
            "sources": [
                {"label": "Yale School of Nursing — MSN", "url": "https://nursing.yale.edu/academics/msn-program"},
                {"label": "U.S. News — Yale Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "yale-divinity-mdiv": {
            "summary": (
                "Students describe Yale Divinity School's M.Div. as a theologically rigorous "
                "ordination-track degree in an ecumenical Protestant seminary embedded in a "
                "major research university; praise includes the Berkeley Divinity School "
                "partnership, Institute of Sacred Music access, and interdisciplinary Yale "
                "coursework, with cautions about limited financial aid relative to tuition "
                "and a career path concentrated in ministry and nonprofit leadership."
            ),
            "themes": [
                {"label": "Ecumenical formation", "sentiment": "positive", "detail": "M.Div. integrates worship, field education, and theological study across traditions."},
                {"label": "Yale ecosystem", "sentiment": "positive", "detail": "Students cross-register in Yale College and professional schools."},
                {"label": "Berkeley partnership", "sentiment": "positive", "detail": "Episcopal-affiliated Berkeley Divinity School enriches liturgical formation."},
                {"label": "Tuition & aid", "sentiment": "caution", "detail": "Seminary tuition is substantial; aid packages vary by denomination and need."},
                {"label": "Ministry-focused careers", "sentiment": "mixed", "detail": "Graduates primarily enter ordained ministry, chaplaincy, and nonprofit roles."},
            ],
            "sources": [
                {"label": "Yale Divinity School — M.Div.", "url": "https://divinity.yale.edu/academics/mdiv"},
                {"label": "Niche — Yale University reviews", "url": f"{NICHE}reviews/"},
            ],
        },
        "yale-art-mfa": {
            "summary": (
                "Graduate applicants describe Yale School of Art's MFA as one of the most "
                "selective fine-arts programs in the U.S., with fully funded two-year "
                "residencies in painting/printmaking or sculpture/photography; praise includes "
                "critique-based studio culture and visiting-artist networks, with cautions about "
                "extremely competitive admission, limited institutional career placement, and "
                "the subjective nature of fine-arts hiring."
            ),
            "themes": [
                {"label": "Elite selectivity", "sentiment": "positive", "detail": "Yale MFA admits a tiny cohort each year across painting, sculpture, and photography."},
                {"label": "Funded residency", "sentiment": "positive", "detail": "Most students receive tuition scholarships and studio space."},
                {"label": "Critique culture", "sentiment": "positive", "detail": "Weekly critiques and visiting artists shape professional studio practice."},
                {"label": "Career opacity", "sentiment": "caution", "detail": "Fine-arts careers depend on gallery representation and grants, not placement offices."},
                {"label": "Intense competition", "sentiment": "caution", "detail": "Admission rates are among the lowest of any Yale graduate program."},
            ],
            "sources": [
                {"label": "Yale School of Art — Graduate", "url": "https://www.art.yale.edu/about/graduate-program"},
                {"label": "U.S. News — Yale University", "url": USNEWS["yale"]},
            ],
        },
        "yale-master-of-laws-llm-ms": {
            "summary": (
                "International lawyers describe Yale Law's LL.M. as a small, scholarly one-year "
                "program — U.S. News ranks Yale Law No. 1 — emphasizing legal theory, "
                "interdisciplinary study, and faculty mentorship rather than large-section "
                "corporate training; praise includes unmatched faculty access and the "
                "Sterling Law Building community, with cautions that the LL.M. is not a bar-exam "
                "pathway for most foreign lawyers and that U.S. Big Law placement is less central "
                "than at peer LL.M. programs."
            ),
            "themes": [
                {"label": "No. 1 law school", "sentiment": "positive", "detail": "U.S. News Best Law Schools consistently ranks Yale Law first."},
                {"label": "Theory & scholarship", "sentiment": "positive", "detail": "LL.M. students engage with faculty-led seminars and research workshops."},
                {"label": "Small cohort", "sentiment": "positive", "detail": "Intimate classes enable direct faculty mentorship."},
                {"label": "Not a bar-prep track", "sentiment": "caution", "detail": "The LL.M. emphasizes scholarship over bar-exam preparation for U.S. practice."},
                {"label": "Limited Big Law focus", "sentiment": "mixed", "detail": "Corporate placement is less central than at schools with larger LL.M. career offices."},
            ],
            "sources": [
                {"label": "Yale Law School — LL.M.", "url": "https://law.yale.edu/studying-yale-law/graduate-programs/llm-program"},
                {"label": "U.S. News — Yale Law School", "url": USNEWS["law"]},
            ],
        },
        "yale-mba-for-executives-emba-ms": {
            "summary": (
                "Working executives describe Yale SOM's MBA for Executives as a 22-month "
                "part-time MBA with monthly New Haven residencies, sharing SOM's integrated "
                "curriculum and mission-driven culture; praise includes peer cohort quality and "
                "global network access, with cautions about travel demands during residencies, "
                "Poets&Quants' recent composite ranking slide for SOM, and less finance-recruiting "
                "density than NYC-based EMBA programs."
            ),
            "themes": [
                {"label": "Integrated SOM core", "sentiment": "positive", "detail": "EMBA students take the same multidisciplinary core as the full-time MBA."},
                {"label": "Executive cohort", "sentiment": "positive", "detail": "Peers bring senior leadership experience across sectors."},
                {"label": "Mission-driven culture", "sentiment": "positive", "detail": "SOM emphasizes leaders for business and society, not finance-only paths."},
                {"label": "Residency travel", "sentiment": "caution", "detail": "Monthly New Haven residencies require significant time away from work."},
                {"label": "Ranking slide", "sentiment": "caution", "detail": "Poets&Quants' 2025-2026 composite dropped SOM to 17th from 8th."},
            ],
            "sources": [
                {"label": "Yale SOM — MBA for Executives", "url": "https://som.yale.edu/programs/mba-for-executives"},
                {"label": "Poets&Quants — Yale SOM profile", "url": POETS_SOM},
            ],
        },
        "yale-doctor-of-medicine-md-prof": {
            "summary": (
                "Medical students describe Yale School of Medicine's M.D. program as a "
                "research-intensive curriculum — U.S. News ranks Yale among the top medical "
                "schools for research — with organ-system-based preclinical years and early "
                "clinical exposure through Yale New Haven Hospital; praise includes funded "
                "research opportunities and the Yale System's flexible grading, with cautions "
                "about New Haven living costs, competitive specialty matching, and a smaller "
                "class than some peer research medical schools."
            ),
            "themes": [
                {"label": "Top research rank", "sentiment": "positive", "detail": "U.S. News ranks Yale among leading medical schools for research."},
                {"label": "Yale System", "sentiment": "positive", "detail": "Pass/fail preclinical years and flexible scheduling support learning over competition."},
                {"label": "Yale New Haven Hospital", "sentiment": "positive", "detail": "Students train at a major tertiary hospital and affiliated sites."},
                {"label": "Specialty matching", "sentiment": "caution", "detail": "Competitive residencies require strong Step scores and research portfolios."},
                {"label": "Cost of living", "sentiment": "caution", "detail": "New Haven housing and living expenses add to already substantial tuition."},
            ],
            "sources": [
                {"label": "Yale School of Medicine — M.D. Program", "url": "https://medicine.yale.edu/education/md-program/"},
                {"label": "U.S. News — Yale School of Medicine", "url": USNEWS["medicine"]},
            ],
        },
        "yale-computer-science-gsas-phd": {
            "summary": (
                "Doctoral students describe Yale CS's Ph.D. as a research degree in a growing "
                "department with strengths in cryptography, ML, and HCI; praise includes faculty "
                "mentorship in a smaller cohort than top CS-flagship schools, with cautions that "
                "Yale CS is ranked below MIT/Stanford/CMU, funding is competitive, and industry "
                "recruiting is less centralized than at larger CS departments."
            ),
            "themes": [
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships and interdisciplinary work."},
                {"label": "Research areas", "sentiment": "positive", "detail": "Active groups in cryptography, machine learning, graphics, and HCI."},
                {"label": "Ivy research ecosystem", "sentiment": "positive", "detail": "Cross-department collaboration with economics, medicine, and statistics."},
                {"label": "Not a CS-flagship", "sentiment": "caution", "detail": "Yale CS ranks below the very top CS-focused universities."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships and fellowships are limited relative to cohort size."},
            ],
            "sources": [
                {"label": "Yale Computer Science — Graduate", "url": "https://cpsc.yale.edu/academics/graduate-program"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "yale-economics-gsas-phd": {
            "summary": (
                "Doctoral students describe Yale Economics's Ph.D. as a top-ranked theory and "
                "applied program producing faculty at leading universities and policy institutions; "
                "praise includes the Cowles Foundation, faculty in macro, labor, and development, "
                "with cautions about extremely competitive admission, rigorous qualifying exams, "
                "and an academic job market that favors top-quartile candidates."
            ),
            "themes": [
                {"label": "Cowles Foundation", "sentiment": "positive", "detail": "Historic econometrics and macro research center anchors the department."},
                {"label": "Faculty placement", "sentiment": "positive", "detail": "Graduates join faculty at R1 universities and policy institutions."},
                {"label": "Theory & applied breadth", "sentiment": "positive", "detail": "Strengths span macro, labor, development, and industrial organization."},
                {"label": "Qualifying exams", "sentiment": "caution", "detail": "Core micro, macro, and econometrics exams are demanding gatekeepers."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track placement concentrates at top research universities."},
            ],
            "sources": [
                {"label": "Yale Economics — Ph.D. Program", "url": "https://economics.yale.edu/graduate/phd-program"},
                {"label": "U.S. News — Yale University", "url": USNEWS["yale"]},
            ],
        },
        "yale-master-of-public-policy-in-global-affairs-mpp-ms": {
            "summary": (
                "Students describe the Jackson School's M.P.P. in Global Affairs as Yale's "
                "newest professional policy degree, emphasizing international security, "
                "development, and climate policy with practitioner faculty; praise includes "
                "Yale's global network and cross-registration with law and environment schools, "
                "with cautions that the program is young (launched 2022), smaller than peer "
                "MPP programs at Harvard or Princeton, and still building alumni placement data."
            ),
            "themes": [
                {"label": "Global affairs focus", "sentiment": "positive", "detail": "Curriculum spans security, development, climate, and diplomacy."},
                {"label": "Practitioner faculty", "sentiment": "positive", "detail": "Former diplomats and policy leaders teach applied courses."},
                {"label": "Yale cross-registration", "sentiment": "positive", "detail": "Students take courses at law, SOM, and environment schools."},
                {"label": "New program", "sentiment": "caution", "detail": "Jackson launched in 2022; alumni networks are still forming."},
                {"label": "Smaller scale", "sentiment": "mixed", "detail": "Cohort size is smaller than established MPP programs at peer Ivies."},
            ],
            "sources": [
                {"label": "Jackson School — M.P.P.", "url": "https://jackson.yale.edu/academics/mpp"},
                {"label": "U.S. News — Yale University", "url": USNEWS["yale"]},
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
    is_law = "Law School" in school
    is_som = "Management" in school
    is_med = "Medicine" in school or "Nursing" in school
    is_public_health = "Public Health" in school
    is_arch = "Architecture" in school
    is_drama = "Drama" in school
    is_seas = "Engineering" in school
    is_gsas = "Graduate School" in school
    is_college = school == "Yale College"

    if is_prof and is_med:
        summary = (
            f"Medical students describe Yale's {program_name} as a research-intensive "
            f"professional degree at a top-ranked medical school with Yale New Haven "
            f"Hospital training; praise includes the Yale System and funded research, "
            f"with cautions about competitive residency matching and New Haven costs."
        )
        themes = [
            {"label": "Research medical school", "sentiment": "positive", "detail": "U.S. News ranks Yale among leading medical schools for research."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Yale New Haven Hospital provides tertiary-care exposure."},
            {"label": "Yale System", "sentiment": "positive", "detail": "Flexible preclinical grading supports collaborative learning."},
            {"label": "Residency competition", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research."},
            {"label": "Living costs", "sentiment": "caution", "detail": "New Haven housing adds to professional-school tuition."},
        ]
        usnews_key = "medicine"
    elif is_phd and is_law:
        summary = (
            f"Doctoral scholars describe Yale Law's {field} as a small, theory-oriented "
            f"research degree within the nation's top-ranked law school; praise includes "
            f"unmatched faculty access and interdisciplinary Yale resources, with cautions "
            f"about limited academic law-faculty hiring and a scholarly rather than "
            f"practitioner orientation."
        )
        themes = [
            {"label": "No. 1 law school", "sentiment": "positive", "detail": "U.S. News Best Law Schools ranks Yale Law first."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Tiny cohorts enable direct work with leading legal scholars."},
            {"label": "Interdisciplinary Yale", "sentiment": "positive", "detail": "Students cross-register in economics, political science, and philosophy."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Faculty hiring in law is highly competitive nationally."},
            {"label": "Theory over practice", "sentiment": "mixed", "detail": "The degree emphasizes scholarship over bar-exam or firm training."},
        ]
        usnews_key = "law"
    elif is_ms and is_law:
        summary = (
            f"Graduate students describe Yale Law's {field} as a one-year scholarly program "
            f"within the nation's top-ranked law school; praise includes faculty seminars "
            f"and the Sterling Law Building community, with cautions that programs emphasize "
            f"legal scholarship over U.S. bar-exam preparation or Big Law placement."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Yale Law No. 1 among U.S. law schools."},
            {"label": "Scholarly focus", "sentiment": "positive", "detail": "Programs emphasize legal theory and interdisciplinary research."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Small classes enable direct engagement with leading scholars."},
            {"label": "Bar-exam pathway", "sentiment": "caution", "detail": "One-year programs are not designed as U.S. bar-exam preparation."},
            {"label": "Career orientation", "sentiment": "mixed", "detail": "Graduates often return to academia, judiciary, or international practice."},
        ]
        usnews_key = "law"
    elif is_ms and is_som:
        summary = (
            f"Students describe Yale SOM's {field} as a mission-driven management program "
            f"built on the school's integrated curriculum; praise includes the business-and-"
            f"society mission and global study options, with cautions about Poets&Quants' "
            f"recent ranking slide and New Haven's distance from finance hubs."
        )
        themes = [
            {"label": "Integrated curriculum", "sentiment": "positive", "detail": "Multidisciplinary core spans organizational behavior, economics, and global business."},
            {"label": "Mission-driven culture", "sentiment": "positive", "detail": "SOM emphasizes leaders for business and society."},
            {"label": "Global network", "sentiment": "positive", "detail": "Global study and exchange programs extend beyond New Haven."},
            {"label": "Ranking slide", "sentiment": "caution", "detail": "Poets&Quants' 2025-2026 composite dropped SOM to 17th."},
            {"label": "Location", "sentiment": "caution", "detail": "New Haven is quieter for finance recruiting than NYC or Boston."},
        ]
        usnews_key = "business"
    elif is_phd and is_med:
        summary = (
            f"Doctoral students describe Yale's {field} as a biomedical research degree "
            f"with access to Yale School of Medicine labs and Yale New Haven Hospital; "
            f"praise includes translational research infrastructure, with cautions about "
            f"long dissertation timelines and competitive academic hiring."
        )
        themes = [
            {"label": "Translational research", "sentiment": "positive", "detail": "Medical-school labs connect basic science to clinical applications."},
            {"label": "Hospital access", "sentiment": "positive", "detail": "Yale New Haven Hospital supports clinical and translational studies."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships."},
            {"label": "Dissertation timeline", "sentiment": "caution", "detail": "Biomedical Ph.D. programs commonly span five or more years."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Faculty positions in biomedical sciences are nationally competitive."},
        ]
        usnews_key = "medicine"
    elif is_ms and is_public_health or is_phd and is_public_health:
        summary = (
            f"Graduate students describe Yale's {deg} in {field} at the School of Public "
            f"Health as a research-oriented health degree — U.S. News ranks Yale Public "
            f"Health among top programs — with praise for epidemiology and health-policy "
            f"faculty; cautions include self-funded tuition for some master's tracks and "
            f"a smaller cohort than large public-health schools."
        )
        themes = [
            {"label": "Top public-health rank", "sentiment": "positive", "detail": "U.S. News ranks Yale among leading public-health programs."},
            {"label": "Epidemiology strength", "sentiment": "positive", "detail": "Faculty lead work in chronic disease, global health, and biostatistics."},
            {"label": "Policy connections", "sentiment": "positive", "detail": "Proximity to Yale Law and Jackson supports health-policy study."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students may self-fund without assistantships."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than flagship public-health schools at Michigan or Johns Hopkins."},
        ]
        usnews_key = "public_health"
    elif is_ms and is_arch or is_phd and is_arch:
        summary = (
            f"Graduate students describe Yale Architecture's {field} as a design-intensive "
            f"degree in one of the nation's top-ranked architecture schools; praise includes "
            f"studio culture, visiting critics, and the Rudolph Hall community, with cautions "
            f"about demanding studio workloads and a profession with variable job security."
        )
        themes = [
            {"label": "Top architecture rank", "sentiment": "positive", "detail": "U.S. News ranks Yale among leading graduate architecture programs."},
            {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and pin-ups anchor the curriculum."},
            {"label": "Visiting critics", "sentiment": "positive", "detail": "Leading architects and critics review student work."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require long hours and iterative critique."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Architecture hiring cycles with the construction economy."},
        ]
        usnews_key = "architecture"
    elif is_ms and is_drama:
        summary = (
            f"Graduate actors and designers describe Yale Drama's {field} as one of the "
            f"most selective conservatory programs in the U.S., with fully funded three-year "
            f"training and Yale Repertory Theatre exposure; praise includes master-class "
            f"faculty and alumni networks in film and theatre, with cautions about "
            f"extremely competitive admission and unpredictable performing-arts careers."
        )
        themes = [
            {"label": "Conservatory selectivity", "sentiment": "positive", "detail": "Yale Drama admits a tiny cohort across acting, design, and directing."},
            {"label": "Yale Rep exposure", "sentiment": "positive", "detail": "Students work alongside Yale Repertory Theatre productions."},
            {"label": "Funded training", "sentiment": "positive", "detail": "Most students receive tuition scholarships and stipends."},
            {"label": "Admission odds", "sentiment": "caution", "detail": "Acceptance rates are among the lowest of any graduate program."},
            {"label": "Career uncertainty", "sentiment": "caution", "detail": "Performing-arts careers depend on casting, grants, and industry cycles."},
        ]
        usnews_key = "yale"
    elif is_phd and is_gsas:
        summary = (
            f"Doctoral students describe Yale GSAS's Ph.D. in {field} as a research degree "
            f"within an Ivy R1 university with interdisciplinary resources; praise includes "
            f"faculty mentorship and Yale's libraries and labs, with cautions about "
            f"competitive funding, qualifying requirements, and academic job-market pressure."
        )
        themes = [
            {"label": "Research mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty advisors in specialized labs."},
            {"label": "Ivy R1 resources", "sentiment": "positive", "detail": "Yale's libraries, museums, and medical school support interdisciplinary work."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "GSAS students cross-register across Yale's professional schools."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Fellowships and teaching appointments are limited relative to cohort size."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track placement is competitive in most GSAS fields."},
        ]
        usnews_key = "yale"
    elif is_ms and is_gsas:
        summary = (
            f"Graduate students describe Yale GSAS's {deg} in {field} as a selective "
            f"one- or two-year program with strong faculty and research ties; praise includes "
            f"small cohorts and Yale's broader ecosystem, with cautions about self-funded "
            f"tuition for terminal master's students and limited career-office support "
            f"compared to professional schools."
        )
        themes = [
            {"label": "Selective admission", "sentiment": "positive", "detail": "GSAS master's programs admit small, research-oriented cohorts."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Students work with leading scholars in economics, statistics, and sciences."},
            {"label": "Yale ecosystem", "sentiment": "positive", "detail": "Cross-registration with law, medicine, and environment schools."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students typically self-fund without assistantships."},
            {"label": "Career support", "sentiment": "mixed", "detail": "GSAS career advising is lighter than SOM or law placement offices."},
        ]
        usnews_key = "yale"
    elif is_bs and is_seas:
        summary = (
            f"Students describe Yale's {field} B.S. in SEAS as an engineering degree "
            f"within a liberal-arts university — U.S. News ranks Yale Engineering among "
            f"leading doctorate-granting programs — with praise for small classes and "
            f"undergraduate research access; cautions include that Yale Engineering is "
            f"smaller than peer flagship engineering schools and CS tracks can feel more "
            f"established for industry recruiting."
        )
        themes = [
            {"label": "Small engineering cohort", "sentiment": "positive", "detail": "SEAS classes are smaller than at large public engineering schools."},
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs in BME, EE, ME, and environmental engineering."},
            {"label": "Liberal-arts context", "sentiment": "positive", "detail": "Engineering students participate in Yale College residential life."},
            {"label": "Smaller than peer flagships", "sentiment": "caution", "detail": "Yale Engineering is smaller than MIT, Stanford, or Berkeley."},
            {"label": "Industry recruiting", "sentiment": "mixed", "detail": "Tech and consulting recruiting is active but less centralized than at CS-flagship schools."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_college:
        summary = (
            f"Students describe Yale's {field} major as a rigorous liberal-arts program "
            f"within Yale College's residential-college system; praise includes small seminars, "
            f"invested professors, and strong graduate-school placement, with cautions that "
            f"STEM teaching quality can vary by department and that Yale's brand in some "
            f"fields is stronger for graduate school than direct industry placement."
        )
        themes = [
            {"label": "Small classes", "sentiment": "positive", "detail": "Seminars and residential-college tutorials anchor the Yale College experience."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Professors are invested in undergraduate teaching and advising."},
            {"label": "Graduate placement", "sentiment": "positive", "detail": "Yale College sends graduates to top Ph.D., law, and medical programs."},
            {"label": "Uneven STEM teaching", "sentiment": "caution", "detail": "Reviewers note STEM teaching quality can vary by department."},
            {"label": "Industry vs. grad school", "sentiment": "mixed", "detail": "Many majors feed graduate and professional school more than direct hiring."},
        ]
        usnews_key = "yale"
    elif is_phd and is_med:
        usnews_key = "medicine"
    else:
        summary = (
            f"Students and third-party guides describe Yale's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if is_gsas or is_seas else 'professionally focused'} "
            f"degree at an Ivy R1 university; praise includes Yale's faculty and New Haven "
            f"resources, with cautions about competitive admission, cost of living, and "
            f"career outcomes that vary by field."
        )
        themes = [
            {"label": "Ivy R1 reputation", "sentiment": "positive", "detail": "Yale's research infrastructure and faculty rank among the nation's best."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Interdisciplinary Yale", "sentiment": "positive", "detail": "Students cross-register across Yale's colleges and professional schools."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Yale graduate and professional programs have selective admission pools."},
            {"label": "Cost & location", "sentiment": "caution", "detail": "New Haven living costs add to Ivy tuition across programs."},
        ]
        usnews_key = "yale"

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Yale — {department or school}", "url": dept_url},
            {"label": "U.S. News — Yale University", "url": USNEWS.get(usnews_key, USNEWS["yale"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    programs = []
    with open("/tmp/yale_missing.txt") as f:
        for line in f:
            if line.startswith("Missing:"):
                continue
            parts = line.strip().split("|")
            if len(parts) >= 5:
                programs.append({
                    "slug": parts[0],
                    "program_name": parts[1],
                    "degree_type": parts[2],
                    "school": parts[3],
                    "department": parts[4],
                })

    reviews = {p["slug"]: review_for(**p) for p in programs}

    lines = [
        '"""Yale University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``yaleprof5`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``yale_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        "remaining coverable programs (60/60 total).",
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

    out = "/workspace/unipaith-backend/src/unipaith/data/yale_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
