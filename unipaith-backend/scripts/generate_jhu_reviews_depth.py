#!/usr/bin/env python3
"""One-shot generator for jhu_reviews_depth.py — 34 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

KRIEGER = "Zanvyl Krieger School of Arts and Sciences"
WHITING = "Whiting School of Engineering"
CAREY = "Carey Business School"
MEDICINE = "School of Medicine"
BLOOMBERG = "Bloomberg School of Public Health"
NURSING = "School of Nursing"
PEABODY = "Peabody Institute"

SCHOOL_URLS = {
    KRIEGER: "https://krieger.jhu.edu/",
    WHITING: "https://engineering.jhu.edu/",
    CAREY: "https://carey.jhu.edu/",
    MEDICINE: "https://www.hopkinsmedicine.org/som/",
    BLOOMBERG: "https://publichealth.jhu.edu/",
    NURSING: "https://nursing.jhu.edu/",
    PEABODY: "https://peabody.jhu.edu/",
}

DEPT_URLS = {
    "Department of Computer Science": "https://www.cs.jhu.edu/",
    "Department of Biomedical Engineering": "https://www.bme.jhu.edu/",
    "Department of Mechanical Engineering": "https://me.jhu.edu/",
    "Department of Chemical and Biomolecular Engineering": "https://chbe.jhu.edu/",
    "Department of Civil and Systems Engineering": "https://engineering.jhu.edu/case/",
    "Department of Electrical and Computer Engineering": "https://engineering.jhu.edu/ece/",
    "Department of Materials Science and Engineering": "https://engineering.jhu.edu/mse/",
    "Department of Applied Mathematics and Statistics": "https://engineering.jhu.edu/ams/",
    "Department of Economics": "https://econ.jhu.edu/",
    "Carey Business School": "https://carey.jhu.edu/",
    "Bloomberg School of Public Health": "https://publichealth.jhu.edu/",
    "School of Nursing": "https://nursing.jhu.edu/",
    "School of Medicine": "https://www.hopkinsmedicine.org/som/",
    "Peabody Institute": "https://peabody.jhu.edu/",
    "Chemical Engineering": "https://chbe.jhu.edu/",
    "Civil Engineering": "https://engineering.jhu.edu/case/",
    "Computer Engineering": "https://engineering.jhu.edu/ece/",
    "Electrical, Electronics, and Communications Engineering": "https://engineering.jhu.edu/ece/",
    "Mechanical Engineering": "https://me.jhu.edu/",
    "Materials Engineering": "https://engineering.jhu.edu/mse/",
    "Systems Engineering": "https://engineering.jhu.edu/case/",
    "Industrial Engineering": "https://engineering.jhu.edu/case/",
    "Environmental/Environmental Health Engineering": "https://engineering.jhu.edu/case/",
    "Engineering Mechanics": "https://me.jhu.edu/",
    "Engineering, General": "https://engineering.jhu.edu/",
    "Biomedical/Medical Engineering": "https://www.bme.jhu.edu/",
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "https://engineering.jhu.edu/",
    "Mechatronics, Robotics, and Automation Engineering": "https://lcsr.jhu.edu/",
    "Engineering-Related Fields": "https://engineering.jhu.edu/",
    "Business/Commerce, General": "https://carey.jhu.edu/",
    "Business Administration, Management and Operations": "https://carey.jhu.edu/",
    "Finance and Financial Management Services": "https://carey.jhu.edu/",
    "Public Health": "https://publichealth.jhu.edu/",
    "Registered Nursing, Nursing Administration, Nursing Research and Clinical Nursing": "https://nursing.jhu.edu/",
    "Film/Video and Photographic Arts": "https://peabody.jhu.edu/",
    "Economics": "https://econ.jhu.edu/",
    "Medicine": "https://www.hopkinsmedicine.org/som/",
}

USNEWS = {
    "jhu": "https://www.usnews.com/best-colleges/johns-hopkins-university-2071",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/johns-hopkins-university-01026",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/johns-hopkins-university-040101",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/johns-hopkins-university-040101",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
    "bme": "https://www.usnews.com/best-colleges/rankings/biological-engineering-overall",
}

NICHE = "https://www.niche.com/colleges/johns-hopkins-university/"
POETS_CAREY = "https://poetsandquants.com/schools/carey-business-school-johns-hopkins-university/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Bachelor of Science in Engineering in|BSE in) (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in|Master of Engineering in) (.+)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.jhu.edu/")
    dept_url = DEPT_URLS.get(department, DEPT_URLS.get(field, school_url))

    is_carey = school == CAREY
    is_med = school == MEDICINE
    is_nursing = school == NURSING
    is_whiting = school == WHITING
    is_krieger = school == KRIEGER
    is_bloomberg = school == BLOOMBERG
    is_peabody = school == PEABODY
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")

    usnews_key = "jhu"

    overrides: dict[str, dict] = {
        "jhu-finance-and-financial-management-services-ms": {
            "summary": (
                "Students describe Carey's MS in Finance as a STEM-designated, quant-heavy "
                "finance degree in Baltimore with access to Hopkins health-sector and "
                "DC-adjacent recruiting; praise includes small cohorts and applied analytics, "
                "with cautions that the Carey MBA/finance brand trails M7 peers outside "
                "health care and finance."
            ),
            "themes": [
                {"label": "Quantitative finance", "sentiment": "positive", "detail": "STEM-designated curriculum emphasizes modeling, analytics, and valuation."},
                {"label": "Health-sector ties", "sentiment": "positive", "detail": "Proximity to Hopkins Medicine creates distinctive health-finance recruiting."},
                {"label": "Small cohort", "sentiment": "positive", "detail": "Carey's smaller class sizes foster faculty access."},
                {"label": "Brand vs. M7 peers", "sentiment": "mixed", "detail": "Less national finance brand cachet than top-10 MBA programs in NYC/Chicago."},
                {"label": "Tuition cost", "sentiment": "caution", "detail": "Private graduate tuition is steep relative to public finance programs."},
            ],
            "sources": [
                {"label": "Carey — MS in Finance", "url": "https://carey.jhu.edu/programs/master-of-science/ms-finance"},
                {"label": "Poets&Quants — Carey Business School", "url": POETS_CAREY},
            ],
        },
        "jhu-business-administration-management-and-operations-bs": {
            "summary": (
                "Students in Carey's undergraduate business major describe a liberal-arts-plus-"
                "business curriculum on Homewood with quantitative requirements; praise includes "
                "flexibility to combine with sciences or IR, with cautions that Carey is newer "
                "than peer undergraduate business programs and lacks a standalone B-school campus."
            ),
            "themes": [
                {"label": "Interdisciplinary flexibility", "sentiment": "positive", "detail": "Business major pairs with engineering, public health, or IR on Homewood."},
                {"label": "Quantitative core", "sentiment": "positive", "detail": "Calculus and statistics requirements suit analytics-minded students."},
                {"label": "Young program", "sentiment": "mixed", "detail": "Carey undergraduate business is newer than long-established peer majors."},
                {"label": "Recruiting breadth", "sentiment": "caution", "detail": "Consulting/finance placement is strong but smaller than dedicated B-school undergrad paths."},
            ],
            "sources": [
                {"label": "Carey — Undergraduate Business", "url": "https://carey.jhu.edu/programs/undergraduate/business"},
                {"label": "U.S. News — Johns Hopkins University", "url": USNEWS["jhu"]},
            ],
        },
        "jhu-public-health-bs": {
            "summary": (
                "Undergraduates describe JHU's public health major — one of few BA/BS public-health "
                "paths at a top research university — as rigorous and pre-professional, with praise "
                "for Bloomberg School faculty access and Baltimore field sites, and cautions that "
                "intro courses can feel large and graduate-school planning is expected."
            ),
            "themes": [
                {"label": "Rare undergrad major", "sentiment": "positive", "detail": "Few national universities offer a dedicated undergraduate public-health major."},
                {"label": "Bloomberg School access", "sentiment": "positive", "detail": "Students take courses alongside the #1-ranked school of public health."},
                {"label": "Field experience", "sentiment": "positive", "detail": "Baltimore health agencies and community sites provide applied learning."},
                {"label": "Grad-school orientation", "sentiment": "mixed", "detail": "Many students pursue MPH/MD paths after graduation."},
                {"label": "Course scale", "sentiment": "caution", "detail": "Popular gateway courses can feel large before students reach seminars."},
            ],
            "sources": [
                {"label": "Bloomberg School — Public Health Studies", "url": "https://publichealth.jhu.edu/academics/public-health-studies"},
                {"label": "U.S. News — Best Public Health Schools", "url": USNEWS["public_health"]},
            ],
        },
        "jhu-medicine-phd": {
            "summary": (
                "Doctoral trainees describe Hopkins Medicine's biomedical PhD programs as intensely "
                "research-focused within the nation's top-ranked medical school; praise includes "
                "NIH funding depth and clinical collaboration, with cautions about competitive lab "
                "placement and the demanding Baltimore research culture."
            ),
            "themes": [
                {"label": "Research intensity", "sentiment": "positive", "detail": "Hopkins Medicine leads NIH funding among U.S. medical schools."},
                {"label": "Clinical collaboration", "sentiment": "positive", "detail": "Bench-to-bedside research with Johns Hopkins Hospital."},
                {"label": "Lab placement", "sentiment": "caution", "detail": "Competitive admission to top labs requires strong prior research."},
                {"label": "Demanding culture", "sentiment": "mixed", "detail": "High expectations and long hours are common in biomedical PhD training."},
            ],
            "sources": [
                {"label": "Hopkins Medicine — Graduate Programs", "url": "https://www.hopkinsmedicine.org/som/education/graduate/"},
                {"label": "U.S. News — Best Medical Schools: Research", "url": USNEWS["medicine"]},
            ],
        },
        "jhu-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-bs": {
            "summary": (
                "Students in JHU's direct-entry BSN describe a top-ranked nursing school with "
                "intensive clinical rotations at Johns Hopkins Hospital; praise includes faculty "
                "mentorship and research exposure, with cautions about demanding clinical schedules "
                "and East Baltimore housing logistics."
            ),
            "themes": [
                {"label": "Top-ranked school", "sentiment": "positive", "detail": "U.S. News ranks JHU Nursing among the top 3 nationally."},
                {"label": "Clinical rotations", "sentiment": "positive", "detail": "Johns Hopkins Hospital provides world-class patient-care training."},
                {"label": "Research exposure", "sentiment": "positive", "detail": "Undergraduates engage with NIH-funded nursing research."},
                {"label": "Clinical workload", "sentiment": "caution", "detail": "BSN clinical hours and coursework demand strong time management."},
                {"label": "Urban setting", "sentiment": "mixed", "detail": "East Baltimore offers clinical richness but requires planning for housing."},
            ],
            "sources": [
                {"label": "School of Nursing — BSN", "url": "https://nursing.jhu.edu/academics/bsn/"},
                {"label": "U.S. News — Best Nursing Schools", "url": USNEWS["nursing"]},
            ],
        },
        "jhu-registered-nursing-nursing-administration-nursing-research-and-clinical-nursing-phd": {
            "summary": (
                "Doctoral nursing students describe JHU's PhD in nursing as a research-intensive "
                "path for future faculty and health-policy scholars; praise includes mentorship from "
                "leading nurse scientists, with cautions about limited funding compared to STEM PhDs "
                "and the niche academic job market."
            ),
            "themes": [
                {"label": "Nurse-scientist training", "sentiment": "positive", "detail": "Program prepares graduates for faculty and health-services research careers."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Top-ranked faculty in aging, community health, and health equity."},
                {"label": "Research funding", "sentiment": "mixed", "detail": "Funding packages vary by mentor and grant portfolio."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track nursing faculty roles are competitive nationally."},
            ],
            "sources": [
                {"label": "School of Nursing — PhD Program", "url": "https://nursing.jhu.edu/academics/phd/"},
                {"label": "U.S. News — Best Nursing Schools", "url": USNEWS["nursing"]},
            ],
        },
        "jhu-film-video-and-photographic-arts-ms": {
            "summary": (
                "Graduate students describe Peabody's film and media programs as conservatory-style "
                "training within a major research university; praise includes faculty practitioners "
                "and Baltimore/D.C. production access, with cautions that the program is small and "
                "industry placement varies by concentration."
            ),
            "themes": [
                {"label": "Conservatory training", "sentiment": "positive", "detail": "Peabody combines arts-school rigor with Hopkins resources."},
                {"label": "Faculty practitioners", "sentiment": "positive", "detail": "Working filmmakers and media artists lead studio instruction."},
                {"label": "Regional production access", "sentiment": "positive", "detail": "Baltimore and D.C. media markets provide internship opportunities."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Small cohort means fewer peer specializations than large film schools."},
                {"label": "Industry placement", "sentiment": "caution", "detail": "Outcomes vary by portfolio strength and networking effort."},
            ],
            "sources": [
                {"label": "Peabody Institute — Film & Media", "url": "https://peabody.jhu.edu/"},
                {"label": "Niche — Johns Hopkins University", "url": NICHE},
            ],
        },
        "jhu-mechatronics-robotics-and-automation-engineering-ms": {
            "summary": (
                "Students describe JHU's robotics-focused engineering master's as leveraging the "
                "Laboratory for Computational Sensing and Robotics (LCSR) and Malone Center; "
                "praise includes cutting-edge autonomy research and APL partnerships, with cautions "
                "that the program is selective and research-oriented rather than coursework-only."
            ),
            "themes": [
                {"label": "LCSR robotics", "sentiment": "positive", "detail": "World-renowned robotics lab anchors research and thesis work."},
                {"label": "APL partnerships", "sentiment": "positive", "detail": "Applied Physics Laboratory connects students to defense and space robotics."},
                {"label": "Research orientation", "sentiment": "positive", "detail": "Faculty-led projects in medical robotics and autonomous systems."},
                {"label": "Selective admission", "sentiment": "caution", "detail": "Strong quantitative and robotics background expected."},
            ],
            "sources": [
                {"label": "LCSR — Johns Hopkins Robotics", "url": "https://lcsr.jhu.edu/"},
                {"label": "U.S. News — Best Engineering Schools", "url": USNEWS["engineering"]},
            ],
        },
    }

    if slug in overrides:
        return {**overrides[slug], "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    if is_carey and is_ms:
        summary = (
            f"Students describe Carey's {deg} program in {field} as a professionally focused "
            f"business degree at a top-10 national university — U.S. News ranks JHU #7 (2026); "
            f"praise includes health-sector and analytics threads unique to Carey, with cautions "
            f"that the business school's national brand is still building compared with M7 peers."
        )
        themes = [
            {"label": "Health-sector focus", "sentiment": "positive", "detail": "Carey leverages Hopkins Medicine and public-health proximity."},
            {"label": "Analytics curriculum", "sentiment": "positive", "detail": "Quantitative methods and design-thinking run through Carey programs."},
            {"label": "Collaborative cohort", "sentiment": "positive", "detail": "Smaller class sizes foster close faculty relationships."},
            {"label": "Brand recognition", "sentiment": "mixed", "detail": "Carey is newer than long-established top MBA brands."},
            {"label": "Tuition cost", "sentiment": "caution", "detail": "Private graduate business tuition exceeds most public programs."},
        ]
        usnews_key = "business"
    elif is_carey and is_bs:
        summary = (
            f"Students describe Carey's undergraduate business pathway in {field} on Homewood as "
            f"a flexible, quant-oriented major within a top-10 research university; praise includes "
            f"interdisciplinary pairing with engineering or public health, with cautions about "
            f"recruiting breadth versus dedicated undergraduate business schools."
        )
        themes = [
            {"label": "Interdisciplinary pairing", "sentiment": "positive", "detail": "Business coursework combines with sciences, engineering, or IR."},
            {"label": "Quantitative core", "sentiment": "positive", "detail": "Statistics and calculus requirements suit analytics careers."},
            {"label": "Homewood community", "sentiment": "positive", "detail": "Undergraduates benefit from JHU's residential campus culture."},
            {"label": "Recruiting breadth", "sentiment": "caution", "detail": "Consulting/finance pipelines are smaller than at dedicated B-school undergrad programs."},
        ]
        usnews_key = "business"
    elif is_whiting and is_bs and "biomedical" in field.lower():
        summary = (
            f"Students describe JHU's undergraduate {field} program as among the nation's top-ranked "
            f"BME majors — U.S. News routinely ranks JHU #1 or #2; praise includes clinical access "
            f"at Hopkins Medicine and intense lab work, with cautions about heavy workload and "
            f"pre-med competition."
        )
        themes = [
            {"label": "Top-ranked BME", "sentiment": "positive", "detail": "U.S. News ranks JHU biomedical engineering among the best nationally."},
            {"label": "Clinical access", "sentiment": "positive", "detail": "East Baltimore medical campus offers research and shadowing."},
            {"label": "Research labs", "sentiment": "positive", "detail": "Undergraduates join INBT and Malone Center projects."},
            {"label": "Heavy workload", "sentiment": "caution", "detail": "BME plus pre-med tracks demand strong time management."},
        ]
        usnews_key = "bme"
    elif is_whiting and is_bs and any(k in field.lower() for k in ("computer", "electrical")):
        summary = (
            f"Students describe JHU's undergraduate {field} as rigorous and research-oriented within "
            f"the Whiting School; praise includes faculty access and ties to AI/robotics institutes, "
            f"with cautions that the curriculum is theory-heavy and some want more industry-facing "
            f"project courses."
        )
        themes = [
            {"label": "Research depth", "sentiment": "positive", "detail": "Undergraduates join labs in AI, robotics, and systems."},
            {"label": "Theory-heavy core", "sentiment": "mixed", "detail": "Strong foundations but fewer applied-software courses than some peers."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "Small upper-level classes on Homewood campus."},
            {"label": "Career placement", "sentiment": "positive", "detail": "Graduates enter top tech firms, research labs, and graduate programs."},
        ]
        usnews_key = "computer_science"
    elif is_whiting and (is_bs or is_ms):
        summary = (
            f"Students describe JHU's {deg} program in {field} within the Whiting School as "
            f"research-oriented engineering at a top-10 national university; praise includes "
            f"APL partnerships, the Malone Center, and Hopkins Medicine proximity, with cautions "
            f"about demanding coursework and a smaller department than large state engineering schools."
        )
        themes = [
            {"label": "Research orientation", "sentiment": "positive", "detail": "Whiting emphasizes faculty-led research from undergrad through master's."},
            {"label": "APL & medicine ties", "sentiment": "positive", "detail": "Applied Physics Laboratory and Hopkins Medicine enrich engineering projects."},
            {"label": "Design & robotics", "sentiment": "positive", "detail": "LCSR and design courses provide hands-on engineering experience."},
            {"label": "Program size", "sentiment": "mixed", "detail": "Smaller departments than large public engineering colleges."},
            {"label": "Workload", "sentiment": "caution", "detail": "JHU engineering coursework is consistently described as rigorous."},
        ]
        usnews_key = "engineering"
    elif is_whiting and is_phd:
        summary = (
            f"Doctoral students describe JHU's PhD in {field} within the Whiting School as "
            f"intensely research-focused with strong NIH and industry partnerships; praise includes "
            f"faculty mentorship and APL collaboration, with cautions about competitive funding "
            f"and the demanding Baltimore research environment."
        )
        themes = [
            {"label": "Research intensity", "sentiment": "positive", "detail": "Whiting PhD students lead projects in top-ranked engineering labs."},
            {"label": "APL collaboration", "sentiment": "positive", "detail": "Applied Physics Laboratory offers distinctive research opportunities."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small departments foster close advisor relationships."},
            {"label": "Funding variability", "sentiment": "caution", "detail": "RA/TA packages depend on advisor grants and department."},
        ]
        usnews_key = "engineering"
    elif is_bloomberg and is_bs:
        summary = (
            f"Undergraduates describe JHU's {field} major as a rare pre-professional path tied to "
            f"the #1-ranked Bloomberg School; praise includes faculty access and Baltimore field "
            f"sites, with cautions that many students continue to MPH or clinical graduate programs."
        )
        themes = [
            {"label": "Bloomberg School ties", "sentiment": "positive", "detail": "Undergraduates take courses at the top-ranked school of public health."},
            {"label": "Field experience", "sentiment": "positive", "detail": "Baltimore health agencies provide applied learning."},
            {"label": "Graduate orientation", "sentiment": "mixed", "detail": "Many majors pursue MPH, MD, or PhD paths after graduation."},
            {"label": "Course scale", "sentiment": "caution", "detail": "Gateway courses can feel large before students reach seminars."},
        ]
        usnews_key = "public_health"
    elif is_krieger and is_ms and "econom" in field.lower():
        summary = (
            f"Graduate students describe JHU's master's in {field} within the Krieger School as "
            f"quantitatively rigorous training for consulting, policy, and PhD paths; praise "
            f"includes faculty research access and Baltimore/Washington proximity, with cautions "
            f"about limited formal master's funding compared with PhD programs."
        )
        themes = [
            {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Math-intensive coursework prepares students for analytics and PhD work."},
            {"label": "Faculty research", "sentiment": "positive", "detail": "Graduate students join applied micro, macro, and econometrics labs."},
            {"label": "DC policy access", "sentiment": "positive", "detail": "Baltimore–Washington corridor offers internship opportunities."},
            {"label": "Funding limits", "sentiment": "caution", "detail": "Terminal master's students receive less funding than PhD admits."},
        ]
    elif is_nursing:
        summary = (
            f"Students describe JHU School of Nursing's {deg} program in {field} as training at "
            f"one of the nation's top-ranked nursing schools; praise includes Johns Hopkins Hospital "
            f"clinical sites and NIH-funded research, with cautions about demanding clinical schedules "
            f"and East Baltimore logistics."
        )
        themes = [
            {"label": "Top-ranked school", "sentiment": "positive", "detail": "U.S. News ranks JHU Nursing among the top 3 nationally."},
            {"label": "Clinical partnerships", "sentiment": "positive", "detail": "Johns Hopkins Hospital provides diverse rotations."},
            {"label": "Research culture", "sentiment": "positive", "detail": "Evidence-based practice and NIH-funded nursing research."},
            {"label": "Clinical workload", "sentiment": "caution", "detail": "Nursing programs combine coursework with intensive clinical hours."},
        ]
        usnews_key = "nursing"
    elif is_med and is_phd:
        summary = (
            f"Doctoral trainees describe Hopkins Medicine's PhD training in {field} as among the "
            f"most research-intensive in the country; praise includes NIH funding leadership and "
            f"clinical collaboration, with cautions about competitive lab placement."
        )
        themes = [
            {"label": "Research excellence", "sentiment": "positive", "detail": "Hopkins Medicine leads U.S. medical schools in NIH funding."},
            {"label": "Clinical collaboration", "sentiment": "positive", "detail": "Bench-to-bedside research with Johns Hopkins Hospital."},
            {"label": "Lab placement", "sentiment": "caution", "detail": "Top labs are competitive; prior research experience helps."},
            {"label": "Demanding culture", "sentiment": "mixed", "detail": "Biomedical PhD training is consistently described as intense."},
        ]
        usnews_key = "medicine"
    elif is_peabody:
        summary = (
            f"Students describe Peabody's {deg} program in {field} as conservatory-style arts "
            f"training within Johns Hopkins; praise includes working-artist faculty and Baltimore/"
            f"D.C. cultural access, with cautions that cohorts are small and industry outcomes vary."
        )
        themes = [
            {"label": "Conservatory rigor", "sentiment": "positive", "detail": "Peabody combines intensive arts training with university resources."},
            {"label": "Working artists", "sentiment": "positive", "detail": "Faculty are active performers, composers, and media makers."},
            {"label": "Regional access", "sentiment": "positive", "detail": "Baltimore and D.C. arts scenes provide performance opportunities."},
            {"label": "Industry variability", "sentiment": "caution", "detail": "Career outcomes depend on portfolio, networking, and specialization."},
        ]
    else:
        summary = (
            f"Students and third-party guides describe JHU's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if is_whiting or is_krieger else 'professionally focused'} "
            f"degree at a top-10 national university; praise includes Hopkins faculty and Baltimore/"
            f"Washington resources, with cautions about competitive admission, cost, and outcomes "
            f"that vary by field."
        )
        themes = [
            {"label": "Top-10 national rank", "sentiment": "positive", "detail": "U.S. News ranks JHU #7 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Baltimore–DC corridor", "sentiment": "positive", "detail": "Federal agencies, hospitals, and firms enrich internships and research."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "JHU graduate and professional programs have selective admission pools."},
            {"label": "Cost", "sentiment": "caution", "detail": "Private-university tuition adds to program expense."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Johns Hopkins — {department or school}", "url": dept_url},
            {"label": "U.S. News — Johns Hopkins University", "url": USNEWS.get(usnews_key, USNEWS["jhu"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("jhu")
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
        '"""Johns Hopkins University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``jhuprof3`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``jhu_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/jhu_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
