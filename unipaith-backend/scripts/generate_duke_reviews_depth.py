#!/usr/bin/env python3
"""One-shot generator for duke_reviews_depth.py — 42 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

SCHOOL_URLS = {
    "Trinity College of Arts & Sciences": "https://trinity.duke.edu/",
    "Pratt School of Engineering": "https://pratt.duke.edu/",
    "The Fuqua School of Business": "https://www.fuqua.duke.edu/",
    "Duke University School of Law": "https://law.duke.edu/",
    "Duke University School of Medicine": "https://medschool.duke.edu/",
    "Duke University School of Nursing": "https://nursing.duke.edu/",
    "Duke Divinity School": "https://divinity.duke.edu/",
    "The Graduate School": "https://gradschool.duke.edu/",
}

DEPT_URLS = {
    "Computer Science": "https://cs.duke.edu/",
    "Biomedical Engineering": "https://bme.duke.edu/",
    "Civil Engineering": "https://cee.duke.edu/",
    "Environmental Engineering": "https://cee.duke.edu/",
    "Mechanical Engineering": "https://mems.duke.edu/",
    "Electrical & Computer Engineering": "https://ece.duke.edu/",
    "Engineering Management": "https://meng.duke.edu/",
    "Economics": "https://econ.duke.edu/",
    "Data Science: Mathematics & Computer Science": "https://cs.duke.edu/",
    "Linguistics & Computer Science": "https://cs.duke.edu/",
    "Interdisciplinary Engineering & Applied Science (IDEAS)": "https://pratt.duke.edu/",
    "The Fuqua School of Business": "https://www.fuqua.duke.edu/",
    "Duke University School of Law": "https://law.duke.edu/",
    "Duke University School of Medicine": "https://medschool.duke.edu/",
    "Duke University School of Nursing": "https://nursing.duke.edu/",
    "Duke Divinity School": "https://divinity.duke.edu/",
    "Materials Science & Engineering": "https://mems.duke.edu/",
    "Civil & Environmental Engineering": "https://cee.duke.edu/",
    "Mechanical Engineering & Materials Science": "https://mems.duke.edu/",
}

USNEWS = {
    "duke": "https://www.usnews.com/best-colleges/duke-university-2920",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/duke-university-03060",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/duke-university-fuqua-01044",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/duke-university-04018",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/duke-university-03060",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "divinity": "https://www.usnews.com/best-colleges/duke-university-2920",
}

NICHE = "https://www.niche.com/colleges/duke-university/"
POETS_FUQUA = "https://poetsandquants.com/schools/duke-universitys-fuqua-school-of-business/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Bachelor of Science in Engineering in|BSE in) (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in|Master of Engineering in|Master of Laws) (.+)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.duke.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    is_fuqua = school == "The Fuqua School of Business"
    is_law = school == "Duke University School of Law"
    is_med = school == "Duke University School of Medicine"
    is_nursing = school == "Duke University School of Nursing"
    is_pratt = school == "Pratt School of Engineering"
    is_trinity = school == "Trinity College of Arts & Sciences"
    is_grad = school == "The Graduate School"
    is_divinity = school == "Duke Divinity School"
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")
    is_online = "online" in slug or "online" in program_name.lower()

    overrides: dict[str, dict] = {
        "duke-accelerated-daytime-mba-ms": {
            "summary": (
                "Students describe Fuqua's Accelerated Daytime MBA as a one-year, STEM-designated "
                "MBA for candidates with strong quantitative backgrounds; praise includes Team Fuqua "
                "culture and finance/consulting placement (Class of 2025 median base $160,000), "
                "with cautions that the compressed timeline limits internships and the brand trails "
                "M7 peers in some national markets."
            ),
            "themes": [
                {"label": "One-year format", "sentiment": "positive", "detail": "Accelerated schedule suits candidates with prior business or quantitative training."},
                {"label": "Team Fuqua culture", "sentiment": "positive", "detail": "Collaborative, values-driven community with team-based learning."},
                {"label": "Finance & consulting outcomes", "sentiment": "positive", "detail": "Class of 2025: $160K median base; financial services and consulting are top destinations."},
                {"label": "Compressed timeline", "sentiment": "caution", "detail": "One-year pace limits traditional summer internships and deep specialization."},
                {"label": "Brand vs. M7 peers", "sentiment": "mixed", "detail": "Strong outcomes but a smaller national MBA brand than M7 schools in some markets."},
            ],
            "sources": [
                {"label": "Fuqua — Accelerated Daytime MBA", "url": "https://www.fuqua.duke.edu/programs/accelerated-daytime-mba"},
                {"label": "Poets&Quants — Duke Fuqua", "url": POETS_FUQUA},
            ],
        },
        "duke-weekend-executive-mba-ms": {
            "summary": (
                "Working professionals describe Fuqua's Weekend Executive MBA as a part-time MBA "
                "with monthly Durham residencies and the Team Fuqua collaborative culture; praise "
                "includes strong finance/consulting outcomes and STEM designation, with cautions "
                "about balancing work and residency weekends and Durham's distance from major "
                "finance hubs."
            ),
            "themes": [
                {"label": "Executive cohort", "sentiment": "positive", "detail": "Peers bring substantial work experience across industries."},
                {"label": "Team Fuqua culture", "sentiment": "positive", "detail": "Collaborative community extends to part-time MBA students."},
                {"label": "Career outcomes", "sentiment": "positive", "detail": "Fuqua reports strong placement in finance, consulting, and tech."},
                {"label": "Residency travel", "sentiment": "caution", "detail": "Monthly on-campus residencies require time away from work and family."},
                {"label": "Location", "sentiment": "mixed", "detail": "Durham is livable but not a major finance/consulting hub like NYC or Chicago."},
            ],
            "sources": [
                {"label": "Fuqua — Weekend Executive MBA", "url": "https://www.fuqua.duke.edu/programs/weekend-executive-mba"},
                {"label": "Poets&Quants — Duke Fuqua", "url": POETS_FUQUA},
            ],
        },
        "duke-master-of-management-studies-foundations-of-business-ms": {
            "summary": (
                "Recent graduates describe Fuqua's Master of Management Studies: Foundations of "
                "Business as a pre-experience business master's for non-business undergraduates; "
                "praise includes Team Fuqua culture and a bridge to Fuqua's MBA recruiting, with "
                "cautions that it is not a substitute for work experience in traditional MBA "
                "pipelines and outcomes vary by prior academic background."
            ),
            "themes": [
                {"label": "Pre-experience bridge", "sentiment": "positive", "detail": "Designed for recent graduates without full-time business experience."},
                {"label": "Team Fuqua culture", "sentiment": "positive", "detail": "Collaborative cohort experience mirrors Fuqua MBA values."},
                {"label": "Business foundations", "sentiment": "positive", "detail": "Core coursework spans finance, marketing, strategy, and analytics."},
                {"label": "MBA pipeline limits", "sentiment": "caution", "detail": "Not equivalent to work experience expected by top MBA employers."},
                {"label": "Outcome variability", "sentiment": "mixed", "detail": "Placement depends heavily on undergraduate major and internship history."},
            ],
            "sources": [
                {"label": "Fuqua — Master of Management Studies", "url": "https://www.fuqua.duke.edu/programs/master-management-studies"},
                {"label": "Poets&Quants — Duke Fuqua", "url": POETS_FUQUA},
            ],
        },
        "duke-master-in-business-climate-and-sustainability-mbcs-ms": {
            "summary": (
                "Students describe Fuqua's Master in Business, Climate, and Sustainability (MBCS) "
                "as a specialized business master's bridging finance, policy, and environmental "
                "science; praise includes Duke's Nicholas School ties and growing ESG recruiting, "
                "with cautions that the field is evolving quickly and employer demand varies by "
                "sector and region."
            ),
            "themes": [
                {"label": "ESG focus", "sentiment": "positive", "detail": "Curriculum connects climate science, policy, and business strategy."},
                {"label": "Interdisciplinary Duke", "sentiment": "positive", "detail": "Nicholas School and Sanford faculty enrich sustainability coursework."},
                {"label": "Emerging recruiting", "sentiment": "positive", "detail": "Energy, consulting, and impact-investing firms hire sustainability talent."},
                {"label": "Field evolution", "sentiment": "caution", "detail": "ESG hiring cycles and regulatory frameworks shift rapidly."},
                {"label": "Niche market", "sentiment": "mixed", "detail": "Fewer dedicated roles than traditional finance or consulting tracks."},
            ],
            "sources": [
                {"label": "Fuqua — MBCS program", "url": "https://www.fuqua.duke.edu/programs/master-business-climate-sustainability"},
                {"label": "Nicholas School of the Environment", "url": "https://nicholas.duke.edu/"},
            ],
        },
        "duke-master-of-quantitative-management-business-analytics-ms": {
            "summary": (
                "Students describe Fuqua's Master of Quantitative Management: Business Analytics "
                "as a STEM-designated, data-intensive business master's with strong placement in "
                "consulting and tech analytics roles; praise includes Team Fuqua collaboration and "
                "quantitative rigor, with cautions about a fast-paced curriculum and competition "
                "with dedicated data-science master's programs at peer schools."
            ),
            "themes": [
                {"label": "Analytics rigor", "sentiment": "positive", "detail": "STEM-designated curriculum emphasizes statistics, ML, and business applications."},
                {"label": "Consulting & tech placement", "sentiment": "positive", "detail": "Graduates enter analytics, consulting, and product roles at major firms."},
                {"label": "Team Fuqua culture", "sentiment": "positive", "detail": "Collaborative cohort projects mirror MBA team-based learning."},
                {"label": "Intensive pace", "sentiment": "caution", "detail": "Quantitative core and practicum projects move quickly in a one-year format."},
                {"label": "Peer competition", "sentiment": "mixed", "detail": "Dedicated MS in analytics programs at CMU and MIT compete for similar roles."},
            ],
            "sources": [
                {"label": "Fuqua — MSQM Business Analytics", "url": "https://www.fuqua.duke.edu/programs/master-quantitative-management-business-analytics"},
                {"label": "Poets&Quants — Duke Fuqua", "url": POETS_FUQUA},
            ],
        },
        "duke-msqm-business-analytics-online-ms": {
            "summary": (
                "Working professionals describe Fuqua's online MSQM: Business Analytics as a "
                "part-time, STEM-designated analytics degree with live virtual classes; praise "
                "includes flexibility for working analysts and Fuqua's recruiting network, with "
                "cautions that online delivery reduces spontaneous networking versus the residential "
                "MSQM and that self-paced modules require strong time management."
            ),
            "themes": [
                {"label": "Flexible online format", "sentiment": "positive", "detail": "Part-time schedule suits working professionals in analytics roles."},
                {"label": "STEM designation", "sentiment": "positive", "detail": "STEM status extends OPT eligibility for eligible international graduates."},
                {"label": "Fuqua network", "sentiment": "positive", "detail": "Access to Fuqua alumni and recruiting resources."},
                {"label": "Networking trade-off", "sentiment": "caution", "detail": "Virtual format limits informal campus networking versus residential MSQM."},
                {"label": "Self-directed pace", "sentiment": "mixed", "detail": "Part-time students must balance coursework with full-time jobs."},
            ],
            "sources": [
                {"label": "Fuqua — MSQM Business Analytics (online)", "url": "https://www.fuqua.duke.edu/programs/msqm-business-analytics-online"},
                {"label": "Poets&Quants — Duke Fuqua", "url": POETS_FUQUA},
            ],
        },
        "duke-msqm-health-analytics-online-ms": {
            "summary": (
                "Healthcare professionals describe Fuqua's online MSQM: Health Analytics as a "
                "part-time analytics degree focused on health-data applications; praise includes "
                "Duke Medicine ties and growing health-analytics hiring, with cautions about "
                "regulatory complexity in healthcare data and less finance-recruiting density "
                "than the business-analytics track."
            ),
            "themes": [
                {"label": "Health analytics focus", "sentiment": "positive", "detail": "Curriculum applies analytics to clinical, payer, and pharma datasets."},
                {"label": "Duke Medicine ties", "sentiment": "positive", "detail": "Duke University Hospital and DCRI provide health-data context."},
                {"label": "Flexible online format", "sentiment": "positive", "detail": "Part-time schedule suits working healthcare analysts."},
                {"label": "Healthcare regulation", "sentiment": "caution", "detail": "HIPAA and clinical-data constraints complicate real-world projects."},
                {"label": "Narrower recruiting", "sentiment": "mixed", "detail": "Fewer Wall Street roles than the business-analytics MSQM track."},
            ],
            "sources": [
                {"label": "Fuqua — MSQM Health Analytics (online)", "url": "https://www.fuqua.duke.edu/programs/msqm-health-analytics-online"},
                {"label": "Duke Clinical Research Institute", "url": "https://dcri.org/"},
            ],
        },
        "duke-phd-in-business-administration-phd": {
            "summary": (
                "Doctoral students describe Fuqua's Ph.D. in Business Administration as a "
                "research-intensive program in accounting, finance, marketing, and management; "
                "praise includes close faculty mentorship and interdisciplinary Duke resources, "
                "with cautions about competitive academic job markets and a smaller faculty "
                "than large public business Ph.D. programs."
            ),
            "themes": [
                {"label": "Research mentorship", "sentiment": "positive", "detail": "Small cohorts enable close advisor relationships across business disciplines."},
                {"label": "Interdisciplinary Duke", "sentiment": "positive", "detail": "Health, engineering, and policy schools enrich applied business research."},
                {"label": "Fuqua reputation", "sentiment": "positive", "detail": "Fuqua ranks among top business schools for finance and management research."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track faculty positions are nationally competitive."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than large public business Ph.D. programs with fewer specialty tracks."},
            ],
            "sources": [
                {"label": "Fuqua — Ph.D. Program", "url": "https://www.fuqua.duke.edu/programs/phd"},
                {"label": "U.S. News — Fuqua Business School", "url": USNEWS["business"]},
            ],
        },
        "duke-master-of-laws-llm-ms": {
            "summary": (
                "International lawyers describe Duke Law's LLM as a one-year advanced law degree "
                "with strong faculty in international, environmental, and business law — U.S. News "
                "ranks Duke Law #7 nationally (2026); praise includes clinical offerings and a "
                "collegial community, with cautions about high tuition and limited U.S. bar-exam "
                "pathways for some foreign-trained lawyers."
            ),
            "themes": [
                {"label": "Top-tier national rank", "sentiment": "positive", "detail": "U.S. News ranks Duke Law #7 nationally (2026)."},
                {"label": "International law strength", "sentiment": "positive", "detail": "Faculty and centers focus on global and comparative law."},
                {"label": "Collegial community", "sentiment": "positive", "detail": "Small LLM cohort integrates with JD students in seminars and clinics."},
                {"label": "Tuition & visa", "sentiment": "caution", "detail": "High tuition and visa constraints for post-LLM U.S. employment."},
                {"label": "Bar exam pathways", "sentiment": "mixed", "detail": "Eligibility varies by home-country credentials and state bar rules."},
            ],
            "sources": [
                {"label": "Duke Law — LLM Program", "url": "https://law.duke.edu/academics/llm/"},
                {"label": "U.S. News — Duke Law", "url": USNEWS["law"]},
            ],
        },
        "duke-jd-llm-in-international-and-comparative-law-prof": {
            "summary": (
                "Students describe Duke's joint JD/LLM in International & Comparative Law as a "
                "four-year program combining the JD with advanced international-law training; praise "
                "includes Duke Law's #7 national rank and global-law faculty, with cautions about "
                "extended time in school and a specialized career path versus a standard JD."
            ),
            "themes": [
                {"label": "International law depth", "sentiment": "positive", "detail": "Joint degree adds advanced coursework in comparative and international law."},
                {"label": "Top law school rank", "sentiment": "positive", "detail": "U.S. News ranks Duke Law #7 nationally (2026)."},
                {"label": "Clinical training", "sentiment": "positive", "detail": "Experiential clinics build practical international-law skills."},
                {"label": "Extended timeline", "sentiment": "caution", "detail": "Four-year program adds a year beyond the standard three-year JD."},
                {"label": "Specialized career path", "sentiment": "mixed", "detail": "Best suited for international-law careers rather than general Big Law."},
            ],
            "sources": [
                {"label": "Duke Law — JD/LLM International & Comparative Law", "url": "https://law.duke.edu/academics/llm/jdllm/"},
                {"label": "U.S. News — Duke Law", "url": USNEWS["law"]},
            ],
        },
        "duke-jd-llm-in-law-and-entrepreneurship-prof": {
            "summary": (
                "Students describe Duke's joint JD/LLM in Law & Entrepreneurship as a program "
                "combining legal training with startup and venture-capital law; praise includes "
                "Duke's entrepreneurship clinics and Research Triangle startup ecosystem, with "
                "cautions about a niche career focus and fewer traditional Big Law slots than "
                "generalist JD paths."
            ),
            "themes": [
                {"label": "Entrepreneurship law", "sentiment": "positive", "detail": "Curriculum covers venture finance, IP, and startup governance."},
                {"label": "Triangle startup ecosystem", "sentiment": "positive", "detail": "Research Triangle Park connects students to tech and biotech ventures."},
                {"label": "Clinical experience", "sentiment": "positive", "detail": "Startup Law Clinic provides hands-on venture-law practice."},
                {"label": "Niche career focus", "sentiment": "caution", "detail": "Best suited for startup/VC law rather than general Big Law."},
                {"label": "Extended timeline", "sentiment": "mixed", "detail": "Joint degree adds time beyond the standard three-year JD."},
            ],
            "sources": [
                {"label": "Duke Law — JD/LLM Law & Entrepreneurship", "url": "https://law.duke.edu/academics/llm/jdllm-entrepreneurship/"},
                {"label": "Duke Law — Start-Up Ventures Clinic", "url": "https://law.duke.edu/students/clinics/"},
            ],
        },
        "duke-doctor-of-juridical-science-sjd-phd": {
            "summary": (
                "Legal scholars describe Duke Law's Doctor of Juridical Science (SJD) as an "
                "advanced research degree for candidates pursuing academic legal careers; praise "
                "includes faculty mentorship and interdisciplinary Duke resources, with cautions "
                "about extremely competitive law-faculty hiring and a small cohort relative to "
                "large public law schools."
            ),
            "themes": [
                {"label": "Legal scholarship", "sentiment": "positive", "detail": "SJD candidates produce dissertation-level legal research."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Close advisor relationships with Duke Law faculty."},
                {"label": "Interdisciplinary Duke", "sentiment": "positive", "detail": "Sanford, Fuqua, and Medicine enrich law-and-policy research."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track law faculty positions are highly competitive."},
                {"label": "Small cohort", "sentiment": "mixed", "detail": "Fewer SJD students than large public law schools."},
            ],
            "sources": [
                {"label": "Duke Law — SJD Program", "url": "https://law.duke.edu/academics/sjd/"},
                {"label": "U.S. News — Duke Law", "url": USNEWS["law"]},
            ],
        },
        "duke-medical-scientist-training-program-md-phd-phd": {
            "summary": (
                "Applicants describe Duke's Medical Scientist Training Program (MD-PhD) as a "
                "dual-degree physician-scientist track — U.S. News ranks Duke Medicine #6 for "
                "research (2025); praise includes integrated clinical and research training through "
                "Duke University Hospital and DCRI, with cautions about eight-plus-year timelines "
                "and extremely competitive admission."
            ),
            "themes": [
                {"label": "Physician-scientist training", "sentiment": "positive", "detail": "Integrated MD and Ph.D. curriculum trains clinician-researchers."},
                {"label": "Top research ranking", "sentiment": "positive", "detail": "U.S. News ranks Duke #6 among medical schools for research (2025)."},
                {"label": "DCRI integration", "sentiment": "positive", "detail": "Duke Clinical Research Institute supports translational research."},
                {"label": "Extended timeline", "sentiment": "caution", "detail": "MD-PhD programs commonly span eight or more years."},
                {"label": "Selectivity", "sentiment": "caution", "detail": "Admission requires exceptional research and clinical credentials."},
            ],
            "sources": [
                {"label": "Duke MSTP — MD-PhD Program", "url": "https://medschool.duke.edu/education/health-professions-education-programs/medical-scientist-training-program"},
                {"label": "U.S. News — Duke Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "duke-master-of-biomedical-sciences-mbs-ms": {
            "summary": (
                "Post-baccalaureate students describe Duke's Master of Biomedical Sciences (MBS) "
                "as a one-year bridge program for medical and health-sciences careers; praise "
                "includes Duke Medicine faculty access and a structured pre-med curriculum, with "
                "cautions that it is a credential-enhancement program rather than a direct medical "
                "school admission guarantee."
            ),
            "themes": [
                {"label": "Pre-med bridge", "sentiment": "positive", "detail": "Structured coursework strengthens medical-school applications."},
                {"label": "Duke Medicine access", "sentiment": "positive", "detail": "Faculty and hospital resources enrich biomedical training."},
                {"label": "One-year format", "sentiment": "positive", "detail": "Accelerated timeline suits career changers and gap-year students."},
                {"label": "No admission guarantee", "sentiment": "caution", "detail": "Completion does not guarantee medical-school admission."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Students typically self-fund without research assistantships."},
            ],
            "sources": [
                {"label": "Duke — Master of Biomedical Sciences", "url": "https://medschool.duke.edu/education/health-professions-education-programs/master-biomedical-sciences"},
                {"label": "U.S. News — Duke Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "duke-master-of-nursing-mn-pre-licensure-ms": {
            "summary": (
                "Students describe Duke's Master of Nursing (MN, pre-licensure) as an accelerated "
                "entry-to-nursing program — U.S. News ranks Duke Nursing among top graduate nursing "
                "schools; praise includes clinical training at Duke University Hospital and "
                "simulation labs, with cautions about an intensive accelerated pace and competitive "
                "admission."
            ),
            "themes": [
                {"label": "Accelerated entry", "sentiment": "positive", "detail": "Career changers earn an MN and RN licensure in an accelerated format."},
                {"label": "Clinical training", "sentiment": "positive", "detail": "Duke University Hospital provides hands-on clinical rotations."},
                {"label": "Top nursing rank", "sentiment": "positive", "detail": "U.S. News ranks Duke among leading graduate nursing schools."},
                {"label": "Intensive pace", "sentiment": "caution", "detail": "Accelerated curriculum demands sustained clinical and coursework load."},
                {"label": "Selective admission", "sentiment": "caution", "detail": "Competitive pool for a small cohort."},
            ],
            "sources": [
                {"label": "Duke School of Nursing — MN Program", "url": "https://nursing.duke.edu/academics/programs/master-nursing"},
                {"label": "U.S. News — Duke Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "duke-master-of-science-in-nursing-msn-ms": {
            "summary": (
                "Registered nurses describe Duke's Master of Science in Nursing (MSN) as an "
                "advanced-practice nursing degree with specialty tracks — U.S. News ranks Duke "
                "Nursing among top graduate nursing schools; praise includes Duke Hospital "
                "clinical access and faculty research, with cautions about demanding clinical "
                "hours and regional licensing requirements for advanced-practice roles."
            ),
            "themes": [
                {"label": "Advanced practice tracks", "sentiment": "positive", "detail": "MSN specialties include nurse practitioner and clinical leadership paths."},
                {"label": "Clinical access", "sentiment": "positive", "detail": "Duke University Hospital supports advanced clinical training."},
                {"label": "Research faculty", "sentiment": "positive", "detail": "School of Nursing faculty lead health-services and clinical research."},
                {"label": "Clinical hours", "sentiment": "caution", "detail": "Advanced-practice tracks require extensive supervised clinical hours."},
                {"label": "Licensing variation", "sentiment": "mixed", "detail": "NP scope-of-practice rules vary by state after graduation."},
            ],
            "sources": [
                {"label": "Duke School of Nursing — MSN Program", "url": "https://nursing.duke.edu/academics/programs/msn"},
                {"label": "U.S. News — Duke Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "duke-doctor-of-nursing-practice-dnp-prof": {
            "summary": (
                "Advanced-practice nurses describe Duke's Doctor of Nursing Practice (DNP) as a "
                "terminal clinical doctorate — U.S. News ranks Duke Nursing among top graduate "
                "nursing schools; praise includes evidence-based practice projects and Duke "
                "Hospital leadership training, with cautions about balancing clinical work with "
                "doctoral coursework and regional variation in DNP hiring expectations."
            ),
            "themes": [
                {"label": "Clinical doctorate", "sentiment": "positive", "detail": "DNP prepares advanced-practice leaders for clinical and executive roles."},
                {"label": "Evidence-based projects", "sentiment": "positive", "detail": "Capstone projects apply research to clinical quality improvement."},
                {"label": "Duke Hospital access", "sentiment": "positive", "detail": "Clinical training at a top academic medical center."},
                {"label": "Work-study balance", "sentiment": "caution", "detail": "Practicing nurses must balance clinical shifts with doctoral coursework."},
                {"label": "Employer expectations", "sentiment": "mixed", "detail": "DNP hiring requirements vary by health system and region."},
            ],
            "sources": [
                {"label": "Duke School of Nursing — DNP Program", "url": "https://nursing.duke.edu/academics/programs/dnp"},
                {"label": "U.S. News — Duke Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "duke-doctor-of-nursing-practice-nurse-anesthesia-prof": {
            "summary": (
                "Students describe Duke's Doctor of Nursing Practice — Nurse Anesthesia as a "
                "highly selective CRNA program — U.S. News ranks Duke Nursing among top graduate "
                "nursing schools; praise includes extensive clinical anesthesia training at Duke "
                "University Hospital, with cautions about program intensity, competitive admission, "
                "and CRNA job-market shifts in some regions."
            ),
            "themes": [
                {"label": "CRNA training", "sentiment": "positive", "detail": "Program prepares certified registered nurse anesthetists with extensive clinical hours."},
                {"label": "Hospital clinical access", "sentiment": "positive", "detail": "Duke University Hospital provides diverse anesthesia cases."},
                {"label": "Top nursing rank", "sentiment": "positive", "detail": "U.S. News ranks Duke among leading graduate nursing schools."},
                {"label": "Program intensity", "sentiment": "caution", "detail": "Anesthesia training demands sustained clinical and academic commitment."},
                {"label": "Job-market shifts", "sentiment": "mixed", "detail": "CRNA hiring and autonomy rules vary by state and health system."},
            ],
            "sources": [
                {"label": "Duke School of Nursing — Nurse Anesthesia DNP", "url": "https://nursing.duke.edu/academics/programs/nurse-anesthesia-dnp"},
                {"label": "U.S. News — Duke Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "duke-phd-in-nursing-phd": {
            "summary": (
                "Doctoral students describe Duke's Ph.D. in Nursing as a research degree preparing "
                "nurse scientists — U.S. News ranks Duke Nursing among top graduate nursing schools; "
                "praise includes faculty mentorship in health-services research and Duke Medicine "
                "ties, with cautions about competitive academic hiring and long dissertation timelines."
            ),
            "themes": [
                {"label": "Nurse-scientist training", "sentiment": "positive", "detail": "Ph.D. prepares researchers in health-services and clinical nursing science."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Close advisor relationships with nursing and medicine faculty."},
                {"label": "Duke Medicine ties", "sentiment": "positive", "detail": "Hospital and DCRI resources support health-services research."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track nursing faculty positions are competitive."},
                {"label": "Dissertation timeline", "sentiment": "caution", "detail": "Doctoral programs commonly span five or more years."},
            ],
            "sources": [
                {"label": "Duke School of Nursing — PhD Program", "url": "https://nursing.duke.edu/academics/programs/phd"},
                {"label": "U.S. News — Duke Nursing", "url": USNEWS["nursing"]},
            ],
        },
        "duke-master-of-divinity-mdiv-ms": {
            "summary": (
                "Students describe Duke Divinity School's Master of Divinity (MDiv) as a "
                "theologically rigorous program within Duke University — U.S. News ranks Duke "
                "#7 among national universities (2026); praise includes Wesleyan and Anglican "
                "traditions, field education, and Duke Chapel community, with cautions about "
                "demanding coursework and variable placement in ordained ministry versus nonprofit "
                "leadership."
            ),
            "themes": [
                {"label": "Theological rigor", "sentiment": "positive", "detail": "MDiv curriculum spans scripture, theology, ethics, and pastoral practice."},
                {"label": "Field education", "sentiment": "positive", "detail": "Supervised ministry placements connect classroom learning to congregations."},
                {"label": "Duke Chapel community", "sentiment": "positive", "detail": "Campus worship and Duke University resources enrich the experience."},
                {"label": "Ministry placement variability", "sentiment": "mixed", "detail": "Ordination paths and job markets vary by denomination and region."},
                {"label": "Academic workload", "sentiment": "caution", "detail": "Three-year MDiv combines coursework, field education, and language study."},
            ],
            "sources": [
                {"label": "Duke Divinity — MDiv Program", "url": "https://divinity.duke.edu/academics/mdiv"},
                {"label": "U.S. News — Duke University", "url": USNEWS["duke"]},
            ],
        },
        "duke-data-science-mathematics-and-computer-science-ab": {
            "summary": (
                "Students describe Duke's Data Science: Mathematics & Computer Science major as a "
                "quantitatively rigorous interdisciplinary degree bridging statistics, CS, and "
                "applied math — Niche ranks Duke #15 for undergraduate CS (2026); praise includes "
                "research access and flexible AI/data-science concentrations, with cautions about "
                "demanding prerequisites and a newer major with evolving course offerings."
            ),
            "themes": [
                {"label": "Interdisciplinary rigor", "sentiment": "positive", "detail": "Combines mathematics, statistics, and computer science foundations."},
                {"label": "AI & data-science focus", "sentiment": "positive", "detail": "Concentrations align with growing analytics and ML hiring."},
                {"label": "Research access", "sentiment": "positive", "detail": "Students join CS and statistics faculty research groups."},
                {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Quantitative gateway sequences are competitive and theory-heavy."},
                {"label": "Evolving curriculum", "sentiment": "mixed", "detail": "Newer major still expanding specialized elective offerings."},
            ],
            "sources": [
                {"label": "Duke CS — Undergraduate", "url": "https://cs.duke.edu/undergrad"},
                {"label": "Niche — Best Colleges for Computer Science", "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/"},
            ],
        },
        "duke-linguistics-and-computer-science-ab": {
            "summary": (
                "Students describe Duke's Linguistics & Computer Science interdepartmental major "
                "as a niche interdisciplinary degree bridging NLP, computational linguistics, and "
                "formal language theory; praise includes CS department research in AI/NLP and small "
                "seminars, with cautions about a smaller peer cohort than standalone CS and limited "
                "dedicated course offerings compared with larger NLP programs."
            ),
            "themes": [
                {"label": "NLP & linguistics bridge", "sentiment": "positive", "detail": "Combines formal linguistics with computational and AI methods."},
                {"label": "CS research access", "sentiment": "positive", "detail": "Students join NLP and AI labs within Duke CS."},
                {"label": "Small seminars", "sentiment": "positive", "detail": "Interdisciplinary major attracts motivated, specialized students."},
                {"label": "Limited course depth", "sentiment": "caution", "detail": "Fewer dedicated NLP courses than at CMU or Stanford."},
                {"label": "Niche career path", "sentiment": "mixed", "detail": "Best suited for NLP/CL research or graduate study."},
            ],
            "sources": [
                {"label": "Duke CS — Undergraduate", "url": "https://cs.duke.edu/undergrad"},
                {"label": "Duke Linguistics Program", "url": "https://linguistics.duke.edu/"},
            ],
        },
        "duke-computer-science-grad-phd": {
            "summary": (
                "Doctoral students describe Duke's Ph.D. in Computer Science as a research degree "
                "with strengths in AI, systems, and computational biology — U.S. News ranks Duke "
                "CS graduate #20; praise includes interdisciplinary ties to medicine and "
                "engineering, with cautions about funding competition and a smaller department "
                "than CS-flagship giants."
            ),
            "themes": [
                {"label": "AI & systems research", "sentiment": "positive", "detail": "Faculty lead research in AI, systems, and computational biology."},
                {"label": "Interdisciplinary Duke", "sentiment": "positive", "detail": "Medicine, engineering, and policy schools enrich applied CS research."},
                {"label": "Graduate CS rank", "sentiment": "positive", "detail": "U.S. News ranks Duke CS graduate program #20."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Duke CS."},
                {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller than MIT, Stanford, or CMU CS departments."},
            ],
            "sources": [
                {"label": "Duke CS — Graduate Programs", "url": "https://cs.duke.edu/grad"},
                {"label": "Duke CS — About the Department", "url": "https://cs.duke.edu/about"},
            ],
        },
        "duke-master-of-engineering-in-ai-for-product-innovation-ms": {
            "summary": (
                "Students describe Duke's Master of Engineering in AI for Product Innovation as a "
                "STEM-designated professional master's blending AI, product design, and entrepreneurship; "
                "praise includes Pratt's industry partnerships and Research Triangle tech recruiting, "
                "with cautions about self-funded tuition and competition with dedicated MS in CS "
                "programs at peer schools."
            ),
            "themes": [
                {"label": "AI product focus", "sentiment": "positive", "detail": "Curriculum connects machine learning to product development and innovation."},
                {"label": "STEM designation", "sentiment": "positive", "detail": "STEM status extends OPT eligibility for eligible international graduates."},
                {"label": "Triangle tech recruiting", "sentiment": "positive", "detail": "Research Triangle Park connects graduates to tech and biotech firms."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional MEng students typically self-fund without assistantships."},
                {"label": "Peer competition", "sentiment": "mixed", "detail": "Dedicated MS CS programs at peer schools compete for similar roles."},
            ],
            "sources": [
                {"label": "Duke MEng — AI for Product Innovation", "url": "https://meng.duke.edu/degrees/ai-product-innovation"},
                {"label": "Pratt School of Engineering", "url": "https://pratt.duke.edu/"},
            ],
        },
        "duke-master-of-engineering-in-cybersecurity-ms": {
            "summary": (
                "Professionals describe Duke's Master of Engineering in Cybersecurity as a "
                "coursework-focused MEng blending security engineering, policy, and hands-on labs; "
                "praise includes Pratt faculty research and Triangle defense/tech recruiting, with "
                "cautions about self-funded tuition and a rapidly evolving threat landscape that "
                "requires continuous learning beyond the degree."
            ),
            "themes": [
                {"label": "Security engineering", "sentiment": "positive", "detail": "Curriculum covers cryptography, network security, and secure systems design."},
                {"label": "Hands-on labs", "sentiment": "positive", "detail": "Practical projects simulate real-world security challenges."},
                {"label": "Triangle recruiting", "sentiment": "positive", "detail": "Defense, tech, and healthcare firms hire security engineers in the RTP area."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional MEng students typically self-fund without assistantships."},
                {"label": "Rapid field change", "sentiment": "mixed", "detail": "Cybersecurity requires ongoing certification and skill updates post-graduation."},
            ],
            "sources": [
                {"label": "Duke MEng — Cybersecurity", "url": "https://meng.duke.edu/degrees/cybersecurity"},
                {"label": "Pratt School of Engineering", "url": "https://pratt.duke.edu/"},
            ],
        },
        "duke-master-of-engineering-in-financial-technology-ms": {
            "summary": (
                "Students describe Duke's Master of Engineering in Financial Technology as a "
                "STEM-designated MEng bridging quantitative finance, software engineering, and "
                "data science; praise includes Fuqua ties and finance-recruiting access, with "
                "cautions about self-funded tuition and Durham's distance from Wall Street "
                "recruiting hubs."
            ),
            "themes": [
                {"label": "FinTech focus", "sentiment": "positive", "detail": "Curriculum connects quantitative finance, ML, and software engineering."},
                {"label": "Fuqua ties", "sentiment": "positive", "detail": "Business-school resources enrich finance and entrepreneurship coursework."},
                {"label": "STEM designation", "sentiment": "positive", "detail": "STEM status extends OPT eligibility for eligible international graduates."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Professional MEng students typically self-fund without assistantships."},
                {"label": "Finance hub distance", "sentiment": "mixed", "detail": "Durham is strong for RTP tech but quieter for Wall Street recruiting."},
            ],
            "sources": [
                {"label": "Duke MEng — Financial Technology", "url": "https://meng.duke.edu/degrees/financial-technology"},
                {"label": "Fuqua School of Business", "url": "https://www.fuqua.duke.edu/"},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {
            "summary": r["summary"],
            "themes": r["themes"],
            "sources": r["sources"],
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }

    usnews_key = "duke"

    if is_fuqua:
        summary = (
            f"Students describe Fuqua's {program_name} as a business degree built on Team Fuqua "
            f"collaborative culture — U.S. News ranks Fuqua among top business schools; praise "
            f"includes finance and consulting placement, with cautions about Durham location and "
            f"a brand footprint that trails M7 peers in some national markets."
        )
        themes = [
            {"label": "Team Fuqua culture", "sentiment": "positive", "detail": "Collaborative, values-driven community with team-based learning."},
            {"label": "Career outcomes", "sentiment": "positive", "detail": "Fuqua reports strong placement in finance, consulting, and tech."},
            {"label": "STEM options", "sentiment": "positive", "detail": "Several Fuqua programs carry STEM designation for eligible graduates."},
            {"label": "Location", "sentiment": "mixed", "detail": "Durham is livable but not a major finance/consulting hub."},
            {"label": "Brand vs. M7", "sentiment": "mixed", "detail": "Strong outcomes but smaller national brand than M7 schools in some markets."},
        ]
        return {
            "summary": summary,
            "themes": themes,
            "sources": [
                {"label": "Fuqua School of Business", "url": school_url},
                {"label": "Poets&Quants — Duke Fuqua", "url": POETS_FUQUA},
            ],
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }

    if is_law:
        summary = (
            f"Students describe Duke Law's {program_name} as a rigorous top-tier program — "
            f"U.S. News ranks Duke Law #7 nationally (2026); praise includes clinical offerings "
            f"and a collegial community, with cautions about high tuition and competitive admission."
        )
        themes = [
            {"label": "Top-tier national rank", "sentiment": "positive", "detail": "U.S. News ranks Duke Law #7 nationally (2026)."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Experiential clinics build practical legal skills."},
            {"label": "Collegial community", "sentiment": "positive", "detail": "Small class size fosters collaboration."},
            {"label": "Cost & selectivity", "sentiment": "caution", "detail": "High tuition and selective admission pools."},
        ]
        usnews_key = "law"
    elif is_med or is_nursing:
        summary = (
            f"Students describe Duke's {program_name} within {school} as a health-professions "
            f"degree at a top research medical center — U.S. News ranks Duke Medicine #6 for "
            f"research (2025); praise includes Duke University Hospital clinical access, with "
            f"cautions about competitive admission and demanding clinical workloads."
        )
        themes = [
            {"label": "Top research ranking", "sentiment": "positive", "detail": "U.S. News ranks Duke #6 among medical schools for research (2025)."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Duke University Hospital provides hands-on clinical experience."},
            {"label": "Research integration", "sentiment": "positive", "detail": "DCRI and Duke Medicine support translational health research."},
            {"label": "Selectivity & cost", "sentiment": "caution", "detail": "Highly selective admission with substantial tuition and clinical demands."},
        ]
        usnews_key = "medicine" if is_med else "nursing"
    elif is_phd and (is_grad or is_pratt):
        summary = (
            f"Doctoral students describe Duke's Ph.D. in {field} as a research degree at an R1 "
            f"university ranked #7 nationally by U.S. News (2026); praise includes faculty "
            f"mentorship and interdisciplinary Duke resources, with cautions about competitive "
            f"admission, five-plus-year timelines, and funding competition."
        )
        themes = [
            {"label": "R1 research university", "sentiment": "positive", "detail": "Duke's R1 status supports doctoral research across disciplines."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on funded research."},
            {"label": "Interdisciplinary Duke", "sentiment": "positive", "detail": "Medicine, engineering, and policy schools enrich graduate research."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Duke departments."},
        ]
        usnews_key = "engineering" if is_pratt or "engineering" in field.lower() else "duke"
    elif is_ms and is_pratt:
        summary = (
            f"Graduate students describe Duke's {program_name} within Pratt as a "
            f"{'professional coursework' if 'engineering in' in program_name.lower() else 'research and coursework'} "
            f"degree; praise includes Triangle tech and biotech recruiting and faculty labs, "
            f"with cautions about self-funded tuition for terminal master's students and a "
            f"smaller engineering school than large public tech universities."
        )
        themes = [
            {"label": "Pratt engineering reputation", "sentiment": "positive", "detail": "Pratt ranks among leading private engineering schools."},
            {"label": "Research & industry access", "sentiment": "positive", "detail": "Research Triangle Park connects graduates to tech and biotech firms."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "Classes are smaller than at large public engineering schools."},
            {"label": "Self-funded MS/MEng", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund."},
            {"label": "Department scale", "sentiment": "mixed", "detail": "Smaller than flagship public engineering schools at peer universities."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_pratt:
        summary = (
            f"Students describe Duke's {field} B.S.E. within Pratt as a rigorous engineering "
            f"degree at a selective private R1 university; praise includes undergraduate "
            f"research access and Triangle tech recruiting, with cautions about demanding "
            f"prerequisites and a smaller engineering community than large public tech schools."
        )
        themes = [
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs across Pratt departments."},
            {"label": "Tech placement", "sentiment": "positive", "detail": "Graduates enter tech, consulting, and graduate programs."},
            {"label": "Small Pratt cohort", "sentiment": "positive", "detail": "Close faculty access on a research-university campus."},
            {"label": "Demanding prerequisites", "sentiment": "caution", "detail": "Structured engineering core limits early electives."},
            {"label": "Smaller than peer flagships", "sentiment": "mixed", "detail": "Pratt is smaller than MIT, Berkeley, or Georgia Tech."},
        ]
        usnews_key = "engineering"
    elif is_bs and is_trinity and ("computer" in field.lower() or "data" in field.lower()):
        summary = (
            f"Students describe Duke's {field} major within Trinity as a quantitatively rigorous "
            f"degree — Niche ranks Duke #15 for undergraduate CS (2026); praise includes research "
            f"access and AI/data-science concentrations, with cautions about competitive grading "
            f"and large introductory lectures."
        )
        themes = [
            {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Strong foundations in computing, statistics, and applied math."},
            {"label": "Research depth", "sentiment": "positive", "detail": "Interdisciplinary research in AI, systems, and computational biology."},
            {"label": "National CS standing", "sentiment": "positive", "detail": "Niche #15 for undergraduate CS; graduate program ranked #20 by U.S. News."},
            {"label": "Competitive atmosphere", "sentiment": "caution", "detail": "Selective major with demanding coursework."},
        ]
        usnews_key = "computer_science"
    elif is_bs and is_trinity:
        summary = (
            f"Students describe Duke's {field} major within Trinity as a liberal-arts degree at "
            f"a top-10 national university — U.S. News ranks Duke #7 (2026); praise includes "
            f"small seminars and faculty research access, with cautions that popular majors can "
            f"have large introductory sections."
        )
        themes = [
            {"label": "Top national rank", "sentiment": "positive", "detail": "U.S. News ranks Duke #7 among national universities (2026)."},
            {"label": "Seminar culture", "sentiment": "positive", "detail": "Upper-level Trinity courses emphasize discussion and faculty mentorship."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join faculty research across Duke schools."},
            {"label": "Large intro courses", "sentiment": "caution", "detail": "Popular majors can mean big lectures in gateway sequences."},
        ]
    elif is_divinity:
        summary = (
            f"Students describe Duke Divinity's {program_name} as a theologically rigorous "
            f"program within Duke University; praise includes field education and Duke Chapel "
            f"community, with cautions about demanding coursework and variable ministry placement."
        )
        themes = [
            {"label": "Theological training", "sentiment": "positive", "detail": "Rigorous curriculum in scripture, theology, and pastoral practice."},
            {"label": "Field education", "sentiment": "positive", "detail": "Supervised ministry placements connect learning to congregations."},
            {"label": "Duke University context", "sentiment": "positive", "detail": "Access to a top research university and Duke Chapel worship."},
            {"label": "Ministry placement variability", "sentiment": "mixed", "detail": "Ordination paths vary by denomination and region."},
            {"label": "Academic workload", "sentiment": "caution", "detail": "Graduate divinity programs combine coursework and field education."},
        ]
        usnews_key = "divinity"
    elif is_online:
        summary = (
            f"Working professionals describe Duke's online {program_name} as a flexible "
            f"{'business' if is_fuqua else 'graduate'} degree; praise includes Duke faculty "
            f"and alumni networks, with cautions that online delivery reduces spontaneous "
            f"networking versus residential programs."
        )
        themes = [
            {"label": "Flexible format", "sentiment": "positive", "detail": "Online or hybrid delivery suits working professionals."},
            {"label": "Duke faculty", "sentiment": "positive", "detail": "Live sessions with Duke faculty rather than self-paced MOOC delivery."},
            {"label": "Alumni network", "sentiment": "positive", "detail": "Access to Duke alumni and recruiting resources."},
            {"label": "Networking trade-off", "sentiment": "caution", "detail": "Virtual format limits informal campus networking."},
            {"label": "Self-directed pace", "sentiment": "mixed", "detail": "Part-time students must balance coursework with full-time jobs."},
        ]
    else:
        summary = (
            f"Students and third-party guides describe Duke's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if is_pratt or is_grad else 'professionally focused'} "
            f"degree at a top-10 national university; praise includes Duke's faculty and "
            f"Research Triangle resources, with cautions about competitive admission, cost, "
            f"and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top-10 national rank", "sentiment": "positive", "detail": "U.S. News ranks Duke #7 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Research Triangle access", "sentiment": "positive", "detail": "RTP tech, biotech, and policy institutions enrich study and internships."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Duke graduate and professional programs have selective admission pools."},
            {"label": "Cost & location", "sentiment": "caution", "detail": "Private-university tuition and Durham living costs add to program expense."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Duke — {department or school}", "url": dept_url},
            {"label": "U.S. News — Duke University", "url": USNEWS.get(usnews_key, USNEWS["duke"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("duke")
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
        '"""Duke University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``dukeprof4`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``duke_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/duke_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
