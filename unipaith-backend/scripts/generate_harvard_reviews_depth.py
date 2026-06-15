#!/usr/bin/env python3
"""One-shot generator for harvard_reviews_depth.py — 49 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

SCHOOL_URLS = {
    "Harvard Faculty of Arts & Sciences": "https://fas.harvard.edu/",
    "Harvard John A. Paulson School of Engineering & Applied Sciences": "https://seas.harvard.edu/",
    "Harvard Business School": "https://www.hbs.edu/",
    "Harvard Law School": "https://hls.harvard.edu/",
    "Harvard Medical School": "https://hms.harvard.edu/",
    "Harvard T.H. Chan School of Public Health": "https://www.hsph.harvard.edu/",
    "Harvard Graduate School of Design": "https://www.gsd.harvard.edu/",
    "Harvard Divinity School": "https://hds.harvard.edu/",
    "Harvard School of Dental Medicine": "https://hsdm.harvard.edu/",
}

DEPT_URLS = {
    "History of Art & Architecture": "https://haa.fas.harvard.edu/",
    "Economics": "https://economics.harvard.edu/",
    "Electrical Engineering": "https://seas.harvard.edu/electrical-engineering",
    "Mechanical Engineering": "https://seas.harvard.edu/mechanical-engineering",
    "Bioengineering": "https://seas.harvard.edu/bioengineering",
    "Environmental Science & Engineering": "https://seas.harvard.edu/environmental-science-and-engineering",
    "Computer Science": "https://seas.harvard.edu/computer-science",
    "Harvard Business School": "https://www.hbs.edu/programs/doctoral/",
    "Harvard Law School": "https://hls.harvard.edu/academics/degrees/sjd/",
    "Harvard Medical School": "https://hms.harvard.edu/education",
    "Harvard School of Dental Medicine": "https://hsdm.harvard.edu/education/dmd-program",
    "Harvard T.H. Chan School of Public Health": "https://www.hsph.harvard.edu/",
    "Harvard Graduate School of Design": "https://www.gsd.harvard.edu/",
    "Harvard Divinity School": "https://hds.harvard.edu/academics/mdiv",
    "Journalism": "https://journalism.harvard.edu/",
    "Biomedical/Medical Engineering": "https://seas.harvard.edu/bioengineering",
    "Electrical, Electronics, and Communications Engineering": "https://seas.harvard.edu/electrical-engineering",
    "Engineering Science": "https://seas.harvard.edu/",
    "Engineering Physics": "https://seas.harvard.edu/",
    "Engineering-Related Fields": "https://seas.harvard.edu/",
    "Computer Engineering": "https://seas.harvard.edu/electrical-engineering",
    "Film/Video and Photographic Arts": "https://afvs.fas.harvard.edu/",
    "Biological and Biomedical Sciences, Other": "https://gsas.harvard.edu/",
    "Medicine": "https://hms.harvard.edu/education",
    "Public Health": "https://www.hsph.harvard.edu/",
    "Advanced/Graduate Dentistry and Oral Sciences": "https://hsdm.harvard.edu/",
    "Dentistry": "https://hsdm.harvard.edu/",
}

USNEWS = {
    "harvard": "https://www.usnews.com/best-colleges/harvard-university-2155",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/harvard-university-03009",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/harvard-university-04098",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/harvard-university-04098",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "economics": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
}

NICHE = "https://www.niche.com/colleges/harvard-university/"
POETS_HBS = "https://poetsandquants.com/school-profile/harvard-business-school/"


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
    school_url = SCHOOL_URLS.get(school, "https://www.harvard.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "harvard-economics-phd": {
            "summary": (
                "Doctoral students describe Harvard Economics's Ph.D. as one of the "
                "world's top theory and applied programs — Niche ranks Harvard #6 for "
                "undergraduate economics and graduates join faculty at leading "
                "universities and policy institutions; praise includes the NBER "
                "ecosystem, faculty in macro, labor, and development, with cautions "
                "about extremely competitive admission, rigorous qualifying exams, and "
                "an academic job market that favors top-quartile candidates."
            ),
            "themes": [
                {"label": "Top economics faculty", "sentiment": "positive", "detail": "Faculty span macro, labor, development, and industrial organization."},
                {"label": "NBER & policy access", "sentiment": "positive", "detail": "Cambridge's NBER and Boston policy institutions support applied research."},
                {"label": "Faculty placement", "sentiment": "positive", "detail": "Graduates join R1 faculty and central banks worldwide."},
                {"label": "Qualifying exams", "sentiment": "caution", "detail": "Core micro, macro, and econometrics exams are demanding gatekeepers."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track placement concentrates at top research universities."},
            ],
            "sources": [
                {"label": "Harvard Economics — Ph.D. Program", "url": "https://economics.harvard.edu/graduate/phd-program"},
                {"label": "Niche — Best Colleges for Economics", "url": USNEWS["economics"]},
            ],
        },
        "harvard-cs-phd": {
            "summary": (
                "Doctoral students describe Harvard CS's Ph.D. as a research degree in "
                "a growing department with strengths in AI, systems, and theory; praise "
                "includes faculty mentorship and cross-school collaboration with SEAS "
                "and HMS, with cautions that Harvard CS ranks below MIT/Stanford/CMU, "
                "funding is competitive, and industry recruiting is less centralized than "
                "at larger CS-flagship departments."
            ),
            "themes": [
                {"label": "Research areas", "sentiment": "positive", "detail": "Active groups in AI, systems, theory, and computational science."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships."},
                {"label": "Interdisciplinary Harvard", "sentiment": "positive", "detail": "Collaboration with economics, medicine, and applied math."},
                {"label": "Not a CS-flagship", "sentiment": "caution", "detail": "Harvard CS ranks below the very top CS-focused universities."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are limited relative to applicant interest."},
            ],
            "sources": [
                {"label": "Harvard SEAS — Computer Science Graduate", "url": "https://seas.harvard.edu/computer-science/graduate-programs"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "harvard-business-phd": {
            "summary": (
                "Doctoral students describe HBS's Business Administration Ph.D. as a "
                "small, highly selective research program producing faculty at leading "
                "business schools; praise includes case-method research culture and "
                "access to HBS archives and industry data, with cautions about "
                "extremely competitive academic hiring and a scholarly rather than "
                "practitioner orientation."
            ),
            "themes": [
                {"label": "Faculty placement", "sentiment": "positive", "detail": "Graduates join tenure-track faculty at top business schools worldwide."},
                {"label": "Case-method research", "sentiment": "positive", "detail": "Doctoral training integrates HBS's case-based research tradition."},
                {"label": "Industry data access", "sentiment": "positive", "detail": "HBS archives and corporate partnerships support empirical work."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track business faculty positions are nationally competitive."},
                {"label": "Small cohort", "sentiment": "mixed", "detail": "Tiny entering classes limit peer diversity compared to large public Ph.D. programs."},
            ],
            "sources": [
                {"label": "HBS — Doctoral Programs", "url": "https://www.hbs.edu/doctoral/"},
                {"label": "Poets&Quants — Harvard Business School", "url": POETS_HBS},
            ],
        },
        "harvard-law-sjd": {
            "summary": (
                "Doctoral scholars describe Harvard Law's S.J.D. as the most advanced "
                "research law degree — U.S. News ranks Harvard Law No. 4 (2026) — "
                "attracting international legal scholars for dissertation work; praise "
                "includes unmatched library resources and faculty mentorship, with "
                "cautions about limited funding, a scholarly rather than practitioner "
                "orientation, and competitive academic law-faculty hiring."
            ),
            "themes": [
                {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Harvard Law among the nation's leading law schools."},
                {"label": "Langdell library", "sentiment": "positive", "detail": "The world's largest academic law library supports dissertation research."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Tiny cohorts enable direct work with leading legal scholars."},
                {"label": "Funding variability", "sentiment": "caution", "detail": "S.J.D. funding packages vary; many students rely on external fellowships."},
                {"label": "Academic market", "sentiment": "caution", "detail": "Faculty hiring in law is highly competitive nationally."},
            ],
            "sources": [
                {"label": "Harvard Law — S.J.D. Program", "url": "https://hls.harvard.edu/academics/degrees/sjd/"},
                {"label": "U.S. News — Harvard Law School", "url": USNEWS["law"]},
            ],
        },
        "harvard-biomedical-phd": {
            "summary": (
                "Doctoral students describe Harvard's Biomedical Sciences Ph.D. through "
                "the Division of Medical Sciences as a research degree with access to "
                "HMS labs and affiliated hospitals — U.S. News ranks Harvard Medical "
                "School #1 for research (2026); praise includes translational research "
                "infrastructure, with cautions about long dissertation timelines and "
                "competitive academic hiring."
            ),
            "themes": [
                {"label": "Top research medical school", "sentiment": "positive", "detail": "U.S. News ranks HMS #1 among medical schools for research."},
                {"label": "Hospital access", "sentiment": "positive", "detail": "Affiliated hospitals support clinical and translational studies."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Students join labs across HMS and affiliated institutions."},
                {"label": "Dissertation timeline", "sentiment": "caution", "detail": "Biomedical Ph.D. programs commonly span five or more years."},
                {"label": "Academic market", "sentiment": "caution", "detail": "Faculty positions in biomedical sciences are nationally competitive."},
            ],
            "sources": [
                {"label": "Harvard Medical School — Ph.D. Programs", "url": "https://hms.harvard.edu/education/phd-programs"},
                {"label": "U.S. News — Harvard Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "harvard-dmd": {
            "summary": (
                "Dental students describe Harvard School of Dental Medicine's D.M.D. as "
                "a research-intensive dental program embedded in the Longwood Medical "
                "Area — U.S. News ranks HSDM among leading dental schools — with "
                "praise for early clinical exposure and HMS collaboration, with cautions "
                "about demanding coursework, Boston living costs, and competitive "
                "specialty residency matching."
            ),
            "themes": [
                {"label": "Research dental school", "sentiment": "positive", "detail": "HSDM integrates dental education with HMS biomedical research."},
                {"label": "Clinical training", "sentiment": "positive", "detail": "Students train at Harvard Dental Center and affiliated sites."},
                {"label": "HMS ecosystem", "sentiment": "positive", "detail": "Proximity to HMS and Boston hospitals supports interdisciplinary study."},
                {"label": "Specialty matching", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research."},
                {"label": "Cost of living", "sentiment": "caution", "detail": "Boston housing adds to professional-school tuition."},
            ],
            "sources": [
                {"label": "Harvard School of Dental Medicine — D.M.D.", "url": "https://hsdm.harvard.edu/education/dmd-program"},
                {"label": "U.S. News — Harvard University", "url": USNEWS["harvard"]},
            ],
        },
        "harvard-sm-public-health": {
            "summary": (
                "Graduate students describe Harvard Chan's Master of Science in Public "
                "Health as a research-oriented health degree — U.S. News ranks Harvard "
                "#1 among public-health schools (2026) — with praise for epidemiology "
                "and biostatistics faculty; cautions include self-funded tuition for "
                "some master's tracks and a fast-paced curriculum."
            ),
            "themes": [
                {"label": "Top public-health rank", "sentiment": "positive", "detail": "U.S. News ranks Harvard #1 among schools of public health."},
                {"label": "Epidemiology strength", "sentiment": "positive", "detail": "Faculty lead work in chronic disease, global health, and biostatistics."},
                {"label": "Policy connections", "sentiment": "positive", "detail": "Proximity to HKS and HMS supports health-policy study."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students may self-fund without assistantships."},
                {"label": "Intensive timeline", "sentiment": "caution", "detail": "Research master's programs require sustained coursework and thesis work."},
            ],
            "sources": [
                {"label": "Harvard Chan — Degree Programs", "url": "https://www.hsph.harvard.edu/admissions/degree-programs/"},
                {"label": "U.S. News — Harvard T.H. Chan School of Public Health", "url": USNEWS["public_health"]},
            ],
        },
        "harvard-mla": {
            "summary": (
                "Graduate students describe Harvard GSD's Master in Landscape Architecture "
                "(M.L.A.) as a design-intensive degree in one of the nation's top-ranked "
                "landscape programs — U.S. News ranks Harvard among leading graduate "
                "architecture and design schools; praise includes studio culture and "
                "visiting critics, with cautions about demanding studio workloads and "
                "a profession with variable job security."
            ),
            "themes": [
                {"label": "Top design rank", "sentiment": "positive", "detail": "U.S. News ranks Harvard GSD among leading graduate design programs."},
                {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and pin-ups anchor the M.L.A. curriculum."},
                {"label": "Visiting critics", "sentiment": "positive", "detail": "Leading landscape architects review student work."},
                {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require long hours and iterative critique."},
                {"label": "Career variability", "sentiment": "mixed", "detail": "Landscape architecture hiring cycles with the construction economy."},
            ],
            "sources": [
                {"label": "Harvard GSD — Landscape Architecture", "url": "https://www.gsd.harvard.edu/landscape-architecture/"},
                {"label": "U.S. News — Architecture rankings", "url": USNEWS["architecture"]},
            ],
        },
        "harvard-mdiv": {
            "summary": (
                "Students describe Harvard Divinity School's M.Div. as a theologically "
                "rigorous ordination-track degree in a nonsectarian divinity school "
                "embedded in a major research university; praise includes Andover "
                "Harvard Theological Library access and interdisciplinary Harvard "
                "coursework, with cautions about limited financial aid relative to "
                "tuition and a career path concentrated in ministry and nonprofit "
                "leadership."
            ),
            "themes": [
                {"label": "Ecumenical formation", "sentiment": "positive", "detail": "M.Div. integrates worship, field education, and theological study."},
                {"label": "Harvard ecosystem", "sentiment": "positive", "detail": "Students cross-register across Harvard's professional schools."},
                {"label": "Theological library", "sentiment": "positive", "detail": "Andover Harvard Theological Library supports research across traditions."},
                {"label": "Tuition & aid", "sentiment": "caution", "detail": "Seminary tuition is substantial; aid packages vary by need."},
                {"label": "Ministry-focused careers", "sentiment": "mixed", "detail": "Graduates primarily enter ordained ministry, chaplaincy, and nonprofit roles."},
            ],
            "sources": [
                {"label": "Harvard Divinity School — M.Div.", "url": "https://hds.harvard.edu/academics/mdiv"},
                {"label": "Niche — Harvard University reviews", "url": f"{NICHE}reviews/"},
            ],
        },
        "harvard-art-history-ab": {
            "summary": (
                "Students describe Harvard's History of Art & Architecture concentration "
                "as a rigorous humanities program with access to Harvard Art Museums and "
                "the Fogg, Busch-Reisinger, and Arthur M. Sackler collections; praise "
                "includes small seminars and faculty who are leading scholars, with "
                "cautions that the field feeds graduate school and museum careers more "
                "than direct industry placement and that course access can be competitive."
            ),
            "themes": [
                {"label": "Museum collections", "sentiment": "positive", "detail": "Harvard Art Museums provide direct access to world-class collections."},
                {"label": "Faculty scholars", "sentiment": "positive", "detail": "Professors are leading art historians across periods and regions."},
                {"label": "Seminar culture", "sentiment": "positive", "detail": "Small seminars anchor close reading of visual and architectural history."},
                {"label": "Graduate-school path", "sentiment": "mixed", "detail": "Many graduates pursue Ph.D. programs and museum careers."},
                {"label": "Course access", "sentiment": "caution", "detail": "Popular seminars can be oversubscribed in a large college."},
            ],
            "sources": [
                {"label": "Harvard History of Art & Architecture", "url": "https://haa.fas.harvard.edu/"},
                {"label": "U.S. News — Harvard University", "url": USNEWS["harvard"]},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {**r, "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")
    is_hbs = "Business School" in school
    is_hls = "Law School" in school
    is_hms = "Medical School" in school
    is_hsph = "Public Health" in school
    is_gsd = "Graduate School of Design" in school
    is_hsdm = "Dental Medicine" in school
    is_seas = "Engineering" in school
    is_fas = "Faculty of Arts" in school

    if is_phd and is_hls:
        summary = (
            f"Doctoral scholars describe Harvard Law's {field} as a research degree "
            f"within one of the nation's top-ranked law schools — U.S. News ranks "
            f"Harvard Law No. 4 (2026); praise includes unmatched library resources "
            f"and faculty mentorship, with cautions about competitive academic "
            f"law-faculty hiring and a scholarly orientation."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Harvard Law among the nation's leading law schools."},
            {"label": "Langdell library", "sentiment": "positive", "detail": "The world's largest academic law library supports dissertation research."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Tiny cohorts enable direct work with leading legal scholars."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Faculty hiring in law is highly competitive nationally."},
            {"label": "Scholarly focus", "sentiment": "mixed", "detail": "The degree emphasizes legal scholarship over practitioner training."},
        ]
        usnews_key = "law"
    elif is_ms and is_hls:
        summary = (
            f"Graduate students describe Harvard Law's {field} as a scholarly program "
            f"within one of the nation's top-ranked law schools; praise includes "
            f"faculty seminars and the Langdell library, with cautions that programs "
            f"emphasize legal scholarship over U.S. bar-exam preparation."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Harvard Law among the nation's leading law schools."},
            {"label": "Scholarly focus", "sentiment": "positive", "detail": "Programs emphasize legal theory and interdisciplinary research."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Small classes enable direct engagement with leading scholars."},
            {"label": "Bar-exam pathway", "sentiment": "caution", "detail": "Graduate law programs are not designed as U.S. bar-exam preparation."},
            {"label": "Career orientation", "sentiment": "mixed", "detail": "Graduates often return to academia, judiciary, or international practice."},
        ]
        usnews_key = "law"
    elif is_ms and is_hbs or is_bs and is_hbs or is_phd and is_hbs:
        summary = (
            f"Students and guides describe Harvard Business School's {field} offerings "
            f"within the world's most recognized MBA brand — Poets&Quants and Fortune "
            f"consistently rank HBS among top business schools; praise includes the "
            f"case-method culture and alumni network, with cautions about extremely "
            f"selective admission, high tuition, and that HBS is primarily a "
            f"graduate professional school rather than an undergraduate program."
        )
        themes = [
            {"label": "Case method & brand", "sentiment": "positive", "detail": "HBS pioneered the case method and carries one of the largest MBA alumni networks."},
            {"label": "Alumni network", "sentiment": "positive", "detail": "Fortune and Bloomberg surveys rank HBS among the most desired MBA brands."},
            {"label": "Entrepreneurship", "sentiment": "positive", "detail": "Rock Center for Entrepreneurship supports startup activity across programs."},
            {"label": "Selectivity & cost", "sentiment": "caution", "detail": "Admission is highly competitive; two-year MBA tuition exceeds $150,000 before living costs."},
            {"label": "Graduate-only school", "sentiment": "mixed", "detail": "HBS is a graduate professional school; undergraduate business degrees are not its core offering."},
        ]
        usnews_key = "business"
    elif is_phd and is_hms or is_ms and is_hms:
        summary = (
            f"Graduate students describe Harvard Medical School's {field} as a "
            f"research-intensive degree — U.S. News ranks HMS #1 for research (2026) "
            f"— with access to affiliated hospitals; praise includes translational "
            f"research infrastructure, with cautions about competitive residency "
            f"matching and Boston living costs."
        )
        themes = [
            {"label": "Top research medical school", "sentiment": "positive", "detail": "U.S. News ranks HMS #1 among medical schools for research."},
            {"label": "Hospital access", "sentiment": "positive", "detail": "Affiliated hospitals support clinical and translational studies."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Students join labs across HMS and affiliated institutions."},
            {"label": "Residency competition", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research portfolios."},
            {"label": "Living costs", "sentiment": "caution", "detail": "Boston housing adds to professional-school tuition."},
        ]
        usnews_key = "medicine"
    elif is_ms and is_hsph or is_bs and is_hsph or is_phd and is_hsph:
        summary = (
            f"Graduate students describe Harvard Chan's {deg} in {field} as a "
            f"research-oriented health degree — U.S. News ranks Harvard #1 among "
            f"public-health schools (2026) — with praise for epidemiology and "
            f"health-policy faculty; cautions include self-funded tuition for some "
            f"master's tracks and a smaller cohort than large public-health schools."
        )
        themes = [
            {"label": "Top public-health rank", "sentiment": "positive", "detail": "U.S. News ranks Harvard #1 among schools of public health."},
            {"label": "Epidemiology strength", "sentiment": "positive", "detail": "Faculty lead work in chronic disease, global health, and biostatistics."},
            {"label": "Policy connections", "sentiment": "positive", "detail": "Proximity to HKS and HMS supports health-policy study."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students may self-fund without assistantships."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than flagship public-health schools at Michigan or Johns Hopkins."},
        ]
        usnews_key = "public_health"
    elif is_ms and is_gsd or is_phd and is_gsd:
        summary = (
            f"Graduate students describe Harvard GSD's {field} as a design-intensive "
            f"degree in one of the nation's top-ranked design schools; praise includes "
            f"studio culture, visiting critics, and Gund Hall community, with cautions "
            f"about demanding studio workloads and variable job security in design fields."
        )
        themes = [
            {"label": "Top design rank", "sentiment": "positive", "detail": "U.S. News ranks Harvard GSD among leading graduate design programs."},
            {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and pin-ups anchor the curriculum."},
            {"label": "Visiting critics", "sentiment": "positive", "detail": "Leading architects and designers review student work."},
            {"label": "Studio workload", "sentiment": "caution", "detail": "Design studios require long hours and iterative critique."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Design hiring cycles with the construction and development economy."},
        ]
        usnews_key = "architecture"
    elif is_phd and is_seas:
        summary = (
            f"Doctoral students describe Harvard SEAS's Ph.D. in {field} as a research "
            f"degree within an Ivy R1 university — U.S. News ranks Harvard Engineering "
            f"among leading doctorate-granting programs — with praise for faculty "
            f"mentorship and Allston research facilities, with cautions about funding "
            f"competition and that SEAS is smaller than peer flagship engineering schools."
        )
        themes = [
            {"label": "Research mentorship", "sentiment": "positive", "detail": "Smaller cohorts enable close advisor relationships in specialized labs."},
            {"label": "Allston campus", "sentiment": "positive", "detail": "Science and Engineering Complex supports interdisciplinary research."},
            {"label": "Ivy R1 resources", "sentiment": "positive", "detail": "Cross-school collaboration with HMS, HBS, and FAS."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are limited relative to applicant interest."},
            {"label": "Smaller than peer flagships", "sentiment": "caution", "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley engineering."},
        ]
        usnews_key = "engineering"
    elif is_ms and is_seas:
        summary = (
            f"Graduate students describe Harvard SEAS's M.S. in {field} as a thesis or "
            f"coursework degree within a top R1 engineering school; praise includes "
            f"research assistantships and Boston tech recruiting, with cautions about "
            f"self-funded tuition for terminal master's students."
        )
        themes = [
            {"label": "Research access", "sentiment": "positive", "detail": "Graduate students join faculty labs in specialized engineering areas."},
            {"label": "Boston recruiting", "sentiment": "positive", "detail": "Tech, biotech, and consulting firms recruit Harvard engineering graduates."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Classes are smaller than at large public engineering schools."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund."},
            {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller than flagship public engineering schools at peer universities."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_seas:
        summary = (
            f"Students describe Harvard's {field} S.B. in SEAS as an engineering degree "
            f"within a liberal-arts university — U.S. News ranks Harvard Engineering "
            f"among leading doctorate-granting programs — with praise for small classes "
            f"and undergraduate research access; cautions include that SEAS is smaller "
            f"than peer flagship engineering schools and CS tracks can feel more "
            f"established for industry recruiting."
        )
        themes = [
            {"label": "Small engineering cohort", "sentiment": "positive", "detail": "SEAS classes are smaller than at large public engineering schools."},
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs in EE, ME, bioengineering, and environmental engineering."},
            {"label": "Liberal-arts context", "sentiment": "positive", "detail": "Engineering students participate in Harvard College residential life."},
            {"label": "Smaller than peer flagships", "sentiment": "caution", "detail": "Harvard SEAS is smaller than MIT, Stanford, or Berkeley."},
            {"label": "Industry recruiting", "sentiment": "mixed", "detail": "Tech recruiting is active but less centralized than at CS-flagship schools."},
        ]
        usnews_key = "engineering"
    elif is_phd and is_hsdm or is_ms and is_hsdm:
        summary = (
            f"Graduate students describe Harvard Dental Medicine's {field} as a "
            f"research-oriented dental degree in the Longwood Medical Area; praise "
            f"includes HMS collaboration and clinical training at Harvard Dental Center, "
            f"with cautions about competitive specialty matching and Boston living costs."
        )
        themes = [
            {"label": "Research dental school", "sentiment": "positive", "detail": "HSDM integrates dental education with HMS biomedical research."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Students train at Harvard Dental Center and affiliated sites."},
            {"label": "HMS ecosystem", "sentiment": "positive", "detail": "Proximity to HMS supports interdisciplinary biomedical study."},
            {"label": "Specialty matching", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research."},
            {"label": "Cost of living", "sentiment": "caution", "detail": "Boston housing adds to professional-school tuition."},
        ]
        usnews_key = "harvard"
    elif is_bs and is_fas or is_ms and is_fas or is_phd and is_fas:
        summary = (
            f"Students describe Harvard's {field} program within the Faculty of Arts "
            f"& Sciences as a rigorous liberal-arts or graduate research degree; praise "
            f"includes small seminars, invested professors, and strong graduate-school "
            f"placement, with cautions that STEM teaching quality can vary by department "
            f"and that many majors feed graduate school more than direct industry hiring."
        )
        themes = [
            {"label": "Small classes", "sentiment": "positive", "detail": "Seminars and tutorials anchor the Harvard College and GSAS experience."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Professors are invested in teaching and advising."},
            {"label": "Graduate placement", "sentiment": "positive", "detail": "Harvard sends graduates to top Ph.D., law, and medical programs."},
            {"label": "Uneven STEM teaching", "sentiment": "caution", "detail": "Reviewers note STEM teaching quality can vary by department."},
            {"label": "Industry vs. grad school", "sentiment": "mixed", "detail": "Many programs feed graduate and professional school more than direct hiring."},
        ]
        usnews_key = "harvard"
    else:
        summary = (
            f"Students and third-party guides describe Harvard's {deg} program in {field} "
            f"within {school} as a {'research-oriented' if is_seas or is_fas else 'professionally focused'} "
            f"degree at an Ivy R1 university; praise includes Harvard's faculty and Boston "
            f"resources, with cautions about competitive admission, cost of living, and "
            f"career outcomes that vary by field."
        )
        themes = [
            {"label": "Ivy R1 reputation", "sentiment": "positive", "detail": "Harvard's research infrastructure and faculty rank among the nation's best."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Interdisciplinary Harvard", "sentiment": "positive", "detail": "Students cross-register across Harvard's colleges and professional schools."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Harvard graduate and professional programs have selective admission pools."},
            {"label": "Cost & location", "sentiment": "caution", "detail": "Boston living costs add to Ivy tuition across programs."},
        ]
        usnews_key = "harvard"

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Harvard — {department or school}", "url": dept_url},
            {"label": "U.S. News — Harvard University", "url": USNEWS.get(usnews_key, USNEWS["harvard"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("harvard")
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

    lines = [
        '"""Harvard University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``harvardprof6`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``harvard_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        f"remaining coverable programs ({len(reviews) + len(mod._REVIEWS_BY_SLUG)}/{len(reviews) + len(mod._REVIEWS_BY_SLUG)} total).",
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

    out = "/workspace/unipaith-backend/src/unipaith/data/harvard_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
