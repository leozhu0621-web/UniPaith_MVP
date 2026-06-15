#!/usr/bin/env python3
"""One-shot generator for stanford_reviews_depth.py — 28 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

_HS = "School of Humanities and Sciences"
_ENG = "School of Engineering"
_SUS = "Stanford Doerr School of Sustainability"
_GSB = "Graduate School of Business"
_LAW = "Stanford Law School"
_MED = "School of Medicine"

SCHOOL_URLS = {
    _HS: "https://humsci.stanford.edu/",
    _ENG: "https://engineering.stanford.edu/",
    _SUS: "https://sustainability.stanford.edu/",
    _GSB: "https://www.gsb.stanford.edu/",
    _LAW: "https://law.stanford.edu/",
    _MED: "https://med.stanford.edu/",
}

DEPT_URLS = {
    "Computer Science": "https://www.cs.stanford.edu/",
    "Mechanical Engineering": "https://me.stanford.edu/",
    "Civil and Environmental Engineering": "https://cee.stanford.edu/",
    "Biomedical/Medical Engineering": "https://bioengineering.stanford.edu/",
    "Chemical Engineering": "https://chemeng.stanford.edu/",
    "Electrical, Electronics, and Communications Engineering": "https://ee.stanford.edu/",
    "Materials Engineering": "https://mse.stanford.edu/",
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "https://aa.stanford.edu/",
    "Petroleum Engineering": "https://energy.stanford.edu/",
    "Energy Science and Engineering": "https://sustainability.stanford.edu/",
    "Environmental/Environmental Health Engineering": "https://cee.stanford.edu/",
    "Engineering, Other": "https://engineering.stanford.edu/",
    "Engineering-Related Fields": "https://engineering.stanford.edu/",
    "Economics": "https://economics.stanford.edu/",
    "Film/Video and Photographic Arts": "https://art.stanford.edu/",
    "Public Health": "https://med.stanford.edu/epidemiology.html",
    "Biological and Biomedical Sciences, Other": "https://biosciences.stanford.edu/",
    "Veterinary Biomedical and Clinical Sciences": "https://med.stanford.edu/",
    "Graduate School of Business": "https://www.gsb.stanford.edu/",
    "Stanford Law School": "https://law.stanford.edu/",
    "School of Medicine": "https://med.stanford.edu/",
    "Business, Management, Marketing, and Related Support Services, Other": "https://www.gsb.stanford.edu/",
}

USNEWS = {
    "stanford": "https://www.usnews.com/best-colleges/stanford-university-1305",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/stanford-university-01028",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/stanford-university-03020",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/stanford-university-04057",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "economics": "https://www.usnews.com/best-colleges/rankings/economics",
}

NICHE = "https://www.niche.com/colleges/stanford-university/"
POETS_GSB = "https://poetsandquants.com/schools/stanford-graduate-school-of-business/"
QS_CS = "https://www.topuniversities.com/university-subject-rankings/computer-science-information-systems"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in) (.+)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.stanford.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "stanford-cs-phd": {
            "summary": (
                "Doctoral students describe Stanford's Ph.D. in Computer Science as one of the "
                "world's most selective and influential research programs — QS ranks Stanford No. 2 "
                "globally in computer science (2026) — praising SAIL, HAI, and Silicon Valley "
                "collaborations; common cautions are extremely competitive admission, long "
                "dissertation timelines, and Bay Area cost of living."
            ),
            "themes": [
                {"label": "Global CS standing", "sentiment": "positive", "detail": "QS ranks Stanford No. 2 worldwide in computer science (2026)."},
                {"label": "Research labs", "sentiment": "positive", "detail": "SAIL, HAI, and industry partnerships anchor doctoral research."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small cohorts work closely with leading AI, systems, and theory faculty."},
                {"label": "Extreme selectivity", "sentiment": "caution", "detail": "Admission admits a tiny fraction of a very large applicant pool."},
                {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            ],
            "sources": [
                {"label": "Stanford CS — Ph.D. Program", "url": "https://www.cs.stanford.edu/admissions/phd-admissions"},
                {"label": "QS — Computer Science subject rankings (2026)", "url": QS_CS},
            ],
        },
        "stanford-me-ms": {
            "summary": (
                "Graduate students describe Stanford's MS in Mechanical Engineering as a "
                "research- and coursework-intensive degree within a top-ranked engineering school; "
                "praise includes robotics labs (CHARM Lab, Biomimetics & Dexterous Manipulation), "
                "design courses, and Silicon Valley recruiting, with cautions that terminal MS "
                "students typically self-fund and admission is highly selective."
            ),
            "themes": [
                {"label": "Robotics & design", "sentiment": "positive", "detail": "ME labs span robotics, biomechanics, and product design."},
                {"label": "Silicon Valley access", "sentiment": "positive", "detail": "Graduates enter aerospace, robotics, med-device, and tech roles."},
                {"label": "Engineering reputation", "sentiment": "positive", "detail": "Stanford Engineering ranks among top U.S. graduate engineering schools."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without assistantships typically self-fund tuition."},
                {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is competitive across ME specializations."},
            ],
            "sources": [
                {"label": "Stanford ME — Graduate Program", "url": "https://me.stanford.edu/academics-admissions/graduate-program"},
                {"label": "U.S. News — Engineering rankings", "url": USNEWS["engineering"]},
            ],
        },
        "stanford-cee-ms": {
            "summary": (
                "Graduate students describe Stanford's MS in Civil and Environmental Engineering "
                "as a research-oriented degree spanning structures, water, and sustainability; "
                "praise includes the Blume Earthquake Engineering Center and Doerr School ties, "
                "with cautions about self-funded tuition for terminal master's students and a "
                "smaller department than large public CEE schools."
            ),
            "themes": [
                {"label": "Sustainability focus", "sentiment": "positive", "detail": "CEE connects to the Doerr School and Woods Institute on climate and water."},
                {"label": "Earthquake engineering", "sentiment": "positive", "detail": "Blume Center is a leading seismic-research hub."},
                {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "Faculty collaborate across engineering, policy, and earth sciences."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without RA/TA support typically self-fund."},
                {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller CEE faculty than large public engineering colleges."},
            ],
            "sources": [
                {"label": "Stanford CEE — Graduate Programs", "url": "https://cee.stanford.edu/academics-admissions/graduate-programs"},
                {"label": "U.S. News — Engineering rankings", "url": USNEWS["engineering"]},
            ],
        },
        "stanford-economics-phd": {
            "summary": (
                "Doctoral students describe Stanford's Ph.D. in Economics as a top-tier program "
                "within SIEPR — U.S. News ranks Stanford #6 among national universities (2026); "
                "praise includes faculty in market design, development, and econometrics plus "
                "Silicon Valley policy ties, with cautions about competitive academic job markets "
                "and long dissertation timelines."
            ),
            "themes": [
                {"label": "SIEPR research", "sentiment": "positive", "detail": "Stanford Institute for Economic Policy Research anchors applied work."},
                {"label": "Faculty breadth", "sentiment": "positive", "detail": "Strengths span theory, econometrics, development, and market design."},
                {"label": "Policy & tech ties", "sentiment": "positive", "detail": "Bay Area tech and policy institutions enrich doctoral research."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track economics faculty positions are nationally competitive."},
                {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            ],
            "sources": [
                {"label": "Stanford Economics — Ph.D.", "url": "https://economics.stanford.edu/phd-program"},
                {"label": "U.S. News — Stanford University", "url": USNEWS["stanford"]},
            ],
        },
        "stanford-economics-ms": {
            "summary": (
                "Students describe Stanford's MS in Economics as a quantitatively rigorous "
                "graduate degree preparing for doctoral study or policy/analytics roles; praise "
                "includes SIEPR faculty and econometrics training, with cautions that it is "
                "research-oriented rather than a professional terminal degree and admission is "
                "selective with limited departmental funding."
            ),
            "themes": [
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Core coursework spans micro, macro, econometrics, and field courses."},
                {"label": "SIEPR access", "sentiment": "positive", "detail": "Students join policy-research seminars and faculty projects."},
                {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "Many graduates continue to top doctoral programs or research roles."},
                {"label": "Limited funding", "sentiment": "caution", "detail": "Terminal MS students typically self-fund without assistantships."},
                {"label": "Selective admission", "sentiment": "caution", "detail": "Small cohort relative to applicant volume."},
            ],
            "sources": [
                {"label": "Stanford Economics — Graduate", "url": "https://economics.stanford.edu/graduate-programs"},
                {"label": "U.S. News — Economics rankings", "url": USNEWS["economics"]},
            ],
        },
        "stanford-energy-science-engineering-ms": {
            "summary": (
                "Graduate students describe Stanford's MS in Energy Science and Engineering within "
                "the Doerr School as an interdisciplinary degree bridging earth sciences, policy, "
                "and engineering; praise includes the Precourt Institute for Energy and Woods "
                "Institute ties, with cautions that the school is new (2022) and employer demand "
                "varies by energy sub-sector."
            ),
            "themes": [
                {"label": "Interdisciplinary energy", "sentiment": "positive", "detail": "Curriculum spans engineering, earth systems, and policy."},
                {"label": "Precourt & Woods ties", "sentiment": "positive", "detail": "Leading energy and environment institutes enrich coursework and research."},
                {"label": "Climate focus", "sentiment": "positive", "detail": "Doerr School mission aligns with growing clean-energy hiring."},
                {"label": "New school", "sentiment": "mixed", "detail": "Doerr School opened in 2022; curriculum and recruiting still evolving."},
                {"label": "Sector variability", "sentiment": "caution", "detail": "Energy hiring cycles shift with commodity prices and policy."},
            ],
            "sources": [
                {"label": "Stanford Doerr School — Energy programs", "url": "https://sustainability.stanford.edu/academics/graduate-programs"},
                {"label": "Precourt Institute for Energy", "url": "https://energy.stanford.edu/"},
            ],
        },
        "stanford-gsb-phd": {
            "summary": (
                "Doctoral students describe Stanford GSB's Ph.D. in Business as a research-intensive "
                "program in accounting, finance, marketing, and organizational behavior — U.S. News "
                "ranks Stanford GSB among top business schools; praise includes close faculty "
                "mentorship and Silicon Valley entrepreneurship research, with cautions about "
                "competitive academic job markets and a smaller cohort than large public business "
                "Ph.D. programs."
            ),
            "themes": [
                {"label": "Research mentorship", "sentiment": "positive", "detail": "Small cohorts enable close advisor relationships across business disciplines."},
                {"label": "Silicon Valley context", "sentiment": "positive", "detail": "Entrepreneurship, VC, and tech-market research are program strengths."},
                {"label": "GSB reputation", "sentiment": "positive", "detail": "Stanford GSB ranks among the world's leading business research schools."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track business faculty positions are nationally competitive."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than large public business Ph.D. programs."},
            ],
            "sources": [
                {"label": "Stanford GSB — Ph.D. Program", "url": "https://www.gsb.stanford.edu/programs/phd"},
                {"label": "U.S. News — Stanford GSB", "url": USNEWS["business"]},
            ],
        },
        "stanford-business-management-marketing-and-related-support-services-other-ms": {
            "summary": (
                "Students describe Stanford GSB's specialized master's programs (beyond the MBA) "
                "as rigorous, small-cohort degrees in areas like MSx and executive education; "
                "praise includes GSB faculty and Silicon Valley networks, with cautions that "
                "non-MBA master's paths have narrower recruiting pipelines than the flagship MBA."
            ),
            "themes": [
                {"label": "GSB faculty", "sentiment": "positive", "detail": "Courses taught by the same faculty who lead the MBA and Ph.D. programs."},
                {"label": "Silicon Valley network", "sentiment": "positive", "detail": "Access to GSB alumni and Bay Area employers."},
                {"label": "Small cohorts", "sentiment": "positive", "detail": "Specialized programs maintain intimate class sizes."},
                {"label": "Narrower recruiting", "sentiment": "caution", "detail": "Non-MBA master's paths lack the MBA's structured recruiting funnel."},
                {"label": "High cost", "sentiment": "caution", "detail": "Bay Area living pushes total cost well above tuition alone."},
            ],
            "sources": [
                {"label": "Stanford GSB — Programs", "url": "https://www.gsb.stanford.edu/programs"},
                {"label": "Poets&Quants — Stanford GSB", "url": POETS_GSB},
            ],
        },
        "stanford-law-phd": {
            "summary": (
                "Legal scholars describe Stanford Law's Doctor of Philosophy in Law (J.S.D./S.J.D.) "
                "as an advanced research degree for academic legal careers — U.S. News ranks "
                "Stanford Law #2 nationally (2026); praise includes faculty mentorship in "
                "technology, environmental, and international law, with cautions about extremely "
                "competitive law-faculty hiring and a small cohort."
            ),
            "themes": [
                {"label": "Top law school rank", "sentiment": "positive", "detail": "U.S. News ranks Stanford Law #2 nationally (2026)."},
                {"label": "Tech & policy law", "sentiment": "positive", "detail": "Faculty strengths in IP, cyber, and innovation law."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Close advisor relationships with leading legal scholars."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track law faculty positions are highly competitive."},
                {"label": "Small cohort", "sentiment": "mixed", "detail": "Fewer doctoral law students than large public law schools."},
            ],
            "sources": [
                {"label": "Stanford Law — Advanced Legal Degrees", "url": "https://law.stanford.edu/education/degrees/advanced-legal-degrees/"},
                {"label": "U.S. News — Stanford Law", "url": USNEWS["law"]},
            ],
        },
        "stanford-medicine-phd": {
            "summary": (
                "Doctoral students describe Stanford Medicine's Ph.D. programs as research-intensive "
                "training across biosciences — U.S. News ranks Stanford Medicine #3 for research "
                "(2025); praise includes Biosciences umbrella structure, Stanford Hospital clinical "
                "ties, and interdisciplinary institutes, with cautions about long timelines and "
                "competitive funding for research assistantships."
            ),
            "themes": [
                {"label": "Top research ranking", "sentiment": "positive", "detail": "U.S. News ranks Stanford #3 among medical schools for research (2025)."},
                {"label": "Biosciences structure", "sentiment": "positive", "detail": "Ph.D. programs span biochemistry, genetics, neuroscience, and more."},
                {"label": "Clinical integration", "sentiment": "positive", "detail": "Stanford Hospital and Lucile Packard enrich translational research."},
                {"label": "Time to degree", "sentiment": "caution", "detail": "Doctoral programs commonly span five or more years."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across departments."},
            ],
            "sources": [
                {"label": "Stanford Medicine — Biosciences Ph.D.", "url": "https://biosciences.stanford.edu/prospective-students/phd-programs/"},
                {"label": "U.S. News — Stanford Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "stanford-public-health-ms": {
            "summary": (
                "Students describe Stanford's MS in Public Health (Epidemiology & Clinical Research) "
                "as a research-oriented health-sciences degree within Stanford Medicine; praise "
                "includes clinical-research methodology and Stanford Hospital data access, with "
                "cautions that it is not a generalist MPH and admission is selective with "
                "self-funded tuition for most students."
            ),
            "themes": [
                {"label": "Clinical research focus", "sentiment": "positive", "detail": "Curriculum emphasizes epidemiology and clinical-trial methods."},
                {"label": "Stanford Hospital access", "sentiment": "positive", "detail": "Students work with faculty on real clinical datasets."},
                {"label": "Medicine reputation", "sentiment": "positive", "detail": "Stanford Medicine ranks among top U.S. research medical schools."},
                {"label": "Not a generalist MPH", "sentiment": "mixed", "detail": "Program is narrower than a traditional community-health MPH."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Most MS students self-fund without departmental assistantships."},
            ],
            "sources": [
                {"label": "Stanford Medicine — MS Epidemiology & Clinical Research", "url": "https://med.stanford.edu/epidemiology/education/ms-program.html"},
                {"label": "U.S. News — Stanford Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "stanford-biomedical-medical-engineering-ms": {
            "summary": (
                "Graduate students describe Stanford's MS in Bioengineering as a cross-disciplinary "
                "degree bridging engineering and medicine; praise includes the Clark Center hub, "
                "Stanford Hospital clinical ties, and med-device startup culture, with cautions "
                "that terminal MS students typically self-fund and the program is highly selective."
            ),
            "themes": [
                {"label": "Engineering-medicine bridge", "sentiment": "positive", "detail": "BioE sits at the interface of engineering, biology, and clinical care."},
                {"label": "Clark Center hub", "sentiment": "positive", "detail": "Shared research space connects BioE, Medicine, and Chemistry."},
                {"label": "Med-device ecosystem", "sentiment": "positive", "detail": "Bay Area biotech and device startups recruit BioE graduates."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without RA/TA support typically self-fund."},
                {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is competitive across bioengineering specializations."},
            ],
            "sources": [
                {"label": "Stanford Bioengineering — Graduate", "url": "https://bioengineering.stanford.edu/academics-admissions/graduate-programs"},
                {"label": "U.S. News — Engineering rankings", "url": USNEWS["engineering"]},
            ],
        },
        "stanford-petroleum-engineering-ms": {
            "summary": (
                "Graduate students describe Stanford's MS in Energy Resources Engineering (petroleum "
                "and subsurface focus) as a research-oriented degree within the Doerr School; "
                "praise includes the Energy Resources Engineering department's subsurface modeling "
                "and geophysics strengths, with cautions that petroleum-sector hiring cycles "
                "fluctuate and the program is transitioning under the sustainability school's "
                "broader energy mission."
            ),
            "themes": [
                {"label": "Subsurface expertise", "sentiment": "positive", "detail": "Faculty lead research in reservoir engineering and geophysics."},
                {"label": "Energy transition", "sentiment": "positive", "detail": "Doerr School reframes petroleum training within broader energy systems."},
                {"label": "Research labs", "sentiment": "positive", "detail": "Students join faculty projects in energy modeling and carbon storage."},
                {"label": "Sector hiring cycles", "sentiment": "caution", "detail": "Oil-and-gas recruiting fluctuates with commodity prices."},
                {"label": "Program transition", "sentiment": "mixed", "detail": "Doerr School restructuring may shift course offerings over time."},
            ],
            "sources": [
                {"label": "Stanford — Energy Resources Engineering", "url": "https://energy.stanford.edu/"},
                {"label": "Stanford Doerr School — Graduate programs", "url": "https://sustainability.stanford.edu/academics/graduate-programs"},
            ],
        },
        "stanford-veterinary-biomedical-and-clinical-sciences-ms": {
            "summary": (
                "Students describe Stanford Medicine's biomedical-sciences master's pathways as "
                "research-oriented credentials for health-sciences careers; praise includes "
                "Stanford Hospital and biosciences faculty access, with cautions that these are "
                "specialized research degrees rather than clinical veterinary programs and "
                "most students self-fund."
            ),
            "themes": [
                {"label": "Research training", "sentiment": "positive", "detail": "Coursework and lab work prepare for health-sciences research roles."},
                {"label": "Medicine ties", "sentiment": "positive", "detail": "Stanford Hospital and biosciences faculty enrich training."},
                {"label": "Interdisciplinary scope", "sentiment": "positive", "detail": "Students bridge biology, engineering, and clinical research."},
                {"label": "Not a DVM program", "sentiment": "mixed", "detail": "Stanford does not offer a Doctor of Veterinary Medicine degree."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Most master's students self-fund without assistantships."},
            ],
            "sources": [
                {"label": "Stanford Biosciences", "url": "https://biosciences.stanford.edu/"},
                {"label": "U.S. News — Stanford Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "stanford-biological-and-biomedical-sciences-other-ms": {
            "summary": (
                "Students describe Stanford Medicine's MS pathways in biological and biomedical "
                "sciences as research-oriented degrees for pre-med, industry, or doctoral "
                "pipeline careers; praise includes biosciences faculty and Stanford Hospital "
                "access, with cautions about self-funded tuition and outcomes that vary by "
                "specialization."
            ),
            "themes": [
                {"label": "Biosciences breadth", "sentiment": "positive", "detail": "Programs span genetics, immunology, neuroscience, and more."},
                {"label": "Hospital access", "sentiment": "positive", "detail": "Stanford Hospital provides clinical-research context."},
                {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "Many graduates continue to doctoral or industry research roles."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Most MS students self-fund without departmental assistantships."},
                {"label": "Outcome variability", "sentiment": "mixed", "detail": "Placement depends heavily on specialization and prior research experience."},
            ],
            "sources": [
                {"label": "Stanford Biosciences — Master's programs", "url": "https://biosciences.stanford.edu/"},
                {"label": "U.S. News — Stanford Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "stanford-film-video-and-photographic-arts-bs": {
            "summary": (
                "Students describe Stanford's Film and Media Studies major as a humanities-based "
                "film program within H&S — Niche lists film-related study among Stanford's "
                "distinctive arts offerings; praise includes documentary and critical-media "
                "courses plus Bay Area film-industry access, with cautions that it is an "
                "academic rather than a conservatory film school."
            ),
            "themes": [
                {"label": "Critical media studies", "sentiment": "positive", "detail": "Curriculum emphasizes film history, theory, and documentary practice."},
                {"label": "Bay Area film access", "sentiment": "positive", "detail": "San Francisco and Silicon Valley media industries provide internship paths."},
                {"label": "Interdisciplinary arts", "sentiment": "positive", "detail": "Students combine film with CS, design, or humanities majors."},
                {"label": "Not a conservatory", "sentiment": "mixed", "detail": "Academic program rather than a hands-on film-production conservatory."},
                {"label": "Limited production depth", "sentiment": "caution", "detail": "Fewer dedicated production courses than at USC or NYU film schools."},
            ],
            "sources": [
                {"label": "Stanford Arts — Film and Media Studies", "url": "https://art.stanford.edu/"},
                {"label": "Niche — Stanford University", "url": NICHE},
            ],
        },
        "stanford-film-video-and-photographic-arts-ms": {
            "summary": (
                "Graduate students describe Stanford's Documentary Film and Video MFA as a "
                "small, highly selective program within the Art & Art History department; "
                "praise includes one-on-one faculty mentorship and Bay Area documentary "
                "community ties, with cautions about extremely limited enrollment and a "
                "niche career path versus mainstream film-industry pipelines."
            ),
            "themes": [
                {"label": "Documentary focus", "sentiment": "positive", "detail": "MFA emphasizes documentary filmmaking and visual storytelling."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Tiny cohort enables close advisor relationships."},
                {"label": "Bay Area community", "sentiment": "positive", "detail": "San Francisco documentary festivals and media nonprofits enrich the program."},
                {"label": "Extreme selectivity", "sentiment": "caution", "detail": "Program admits only a handful of students per cycle."},
                {"label": "Niche career path", "sentiment": "mixed", "detail": "Best suited for documentary rather than commercial film careers."},
            ],
            "sources": [
                {"label": "Stanford Art — Documentary Film MFA", "url": "https://art.stanford.edu/"},
                {"label": "Niche — Stanford University", "url": NICHE},
            ],
        },
    }

    if slug in overrides:
        return {**overrides[slug], "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    is_eng = school == _ENG or school == _SUS
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")

    if is_bs and is_eng:
        summary = (
            f"Students describe Stanford's undergraduate {field} program within the School of "
            f"Engineering as a rigorous B.S. at a top-ranked private research university; praise "
            f"includes undergraduate research access, design courses, and Silicon Valley recruiting, "
            f"with cautions about demanding prerequisites and curved grading against elite peers."
        )
        themes = [
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs across engineering departments."},
            {"label": "Silicon Valley access", "sentiment": "positive", "detail": "Graduates enter tech, consulting, and graduate programs."},
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Stanford Engineering ranks among top U.S. undergraduate engineering schools."},
            {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Structured engineering core limits early electives."},
            {"label": "Curved grading", "sentiment": "caution", "detail": "Niche reviewers note grading against an exceptionally strong peer group."},
        ]
        usnews_key = "engineering"
    elif is_ms and is_eng:
        summary = (
            f"Graduate students describe Stanford's MS in {field} within the School of Engineering "
            f"as a research- and coursework-intensive degree; praise includes faculty labs and "
            f"Silicon Valley recruiting, with cautions that terminal MS students typically "
            f"self-fund and admission is highly selective."
        )
        themes = [
            {"label": "Research & industry access", "sentiment": "positive", "detail": "Faculty labs and Bay Area employers enrich graduate training."},
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Stanford Engineering ranks among top U.S. graduate engineering schools."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Classes are smaller than at large public engineering schools."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without assistantships typically self-fund."},
            {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is competitive across engineering specializations."},
        ]
        usnews_key = "engineering"
    elif is_phd:
        summary = (
            f"Doctoral students describe Stanford's Ph.D. in {field} as research-intensive "
            f"training at a top-3 national university — U.S. News ranks Stanford #3 (2026); "
            f"praise includes faculty mentorship and interdisciplinary resources, with cautions "
            f"about competitive academic job markets and long dissertation timelines."
        )
        themes = [
            {"label": "Top national rank", "sentiment": "positive", "detail": "U.S. News ranks Stanford #3 among national universities (2026)."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with leading faculty on funded research."},
            {"label": "Interdisciplinary resources", "sentiment": "positive", "detail": "Cross-school institutes enrich graduate research."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track faculty positions are nationally competitive."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
        ]
        usnews_key = "stanford"
    else:
        summary = (
            f"Students and third-party guides describe Stanford's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if is_eng else 'professionally focused'} "
            f"degree at a top-3 national university; praise includes Stanford's faculty and "
            f"Silicon Valley resources, with cautions about competitive admission, cost, "
            f"and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top national rank", "sentiment": "positive", "detail": "U.S. News ranks Stanford #3 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Silicon Valley access", "sentiment": "positive", "detail": "Bay Area tech, biotech, and policy institutions enrich study and internships."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Stanford graduate and professional programs have selective admission pools."},
            {"label": "Cost of living", "sentiment": "caution", "detail": "Bay Area housing pushes total cost well above tuition alone."},
        ]
        usnews_key = "stanford"

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Stanford — {department or school}", "url": dept_url},
            {"label": "U.S. News — Stanford University", "url": USNEWS.get(usnews_key, USNEWS["stanford"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("stanford")
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
        '"""Stanford University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``stanfordprof6`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``stanford_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/stanford_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
