"""Northwestern University external_reviews depth pass.

Depth pass date: 2026-06-15. Consumed by the ``northwesternprof2`` migration to merge
``DEPTH_REVIEWS`` into ``northwestern_profile._REVIEWS_BY_SLUG`` for 48
remaining coverable programs (58/58 total).
"""

from __future__ import annotations

# ruff: noqa: E501

_DISCLAIMER = (
    "Aggregated and paraphrased from public third-party sources — not "
    "individual verbatim reviews."
)

DEPTH_REVIEWS: dict[str, dict] = {
    "northwestern-advanced-graduate-dentistry-and-oral-sciences-ms": {
        "summary": "Graduate students describe Feinberg's graduate program in in Advanced/Graduate Dentistry and Oral Sciences as a research-intensive health-sciences degree with access to Northwestern Memorial Hospital and Shirley Ryan AbilityLab \u2014 U.S. News ranks Feinberg among top research medical schools; praise includes translational research infrastructure, with cautions about competitive residency matching and Chicago living costs.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Feinberg among leading medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Northwestern Memorial and affiliated sites support clinical research.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students join labs spanning basic science and clinical trials.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Chicago housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Advanced/Graduate Dentistry and Oral Sciences",
                "url": "https://www.feinberg.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-04094",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-architecture-and-related-services-other-bs": {
        "summary": "Students describe Northwestern's undergraduate program in Architecture and Related Services, Other within Weinberg as a liberal-arts degree at a top-10 national university \u2014 U.S. News ranks Northwestern #7 (2026); praise includes small seminars, faculty research access, and Chicago internships, with cautions that popular majors can have large introductory sections.",
        "themes": [
            {
                "label": "Top national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Northwestern #7 among national universities (2026).",
            },
            {
                "label": "Seminar culture",
                "sentiment": "positive",
                "detail": "Upper-level Weinberg courses emphasize discussion and faculty mentorship.",
            },
            {
                "label": "Chicago access",
                "sentiment": "positive",
                "detail": "Internships and research opportunities extend beyond the Evanston campus.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Popular majors can mean big lectures in gateway sequences.",
            },
            {
                "label": "Grad-school path",
                "sentiment": "mixed",
                "detail": "Many humanities and social-science majors pursue further graduate study.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Architecture and Related Services, Other",
                "url": "https://www.architecture.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-biomedical-medical-engineering-ms": {
        "summary": "Graduate students describe Northwestern's biomedical engineering M.S. within McCormick as a research-intensive degree with access to Feinberg and the Shirley Ryan AbilityLab; praise includes translational med-tech projects and Chicago hospital partnerships, with cautions about self-funded tuition for terminal master's students and competitive research funding.",
        "themes": [
            {
                "label": "Clinical translation",
                "sentiment": "positive",
                "detail": "Feinberg and Shirley Ryan AbilityLab partnerships support med-device research.",
            },
            {
                "label": "Interdisciplinary labs",
                "sentiment": "positive",
                "detail": "Students join bioelectronics, imaging, and regenerative-medicine groups.",
            },
            {
                "label": "Chicago med-tech",
                "sentiment": "positive",
                "detail": "Graduates enter med-device firms, hospital R&D, and Ph.D. programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick and Feinberg.",
            },
        ],
        "sources": [
            {
                "label": "McCormick \u2014 Biomedical Engineering Graduate",
                "url": "https://www.mccormick.northwestern.edu/biomedical-engineering/graduate/",
            },
            {
                "label": "U.S. News \u2014 Northwestern Engineering",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-business-commerce-general-bs": {
        "summary": "Students and guides describe Kellogg's undergraduate offerings in Business/Commerce, General within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-business-commerce-general-ms": {
        "summary": "Students and guides describe Kellogg's graduate offerings in in Business/Commerce, General within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-business-management-marketing-and-related-support-services-other-ms": {
        "summary": "Students and guides describe Kellogg's graduate offerings in in Business, Management, Marketing, and Related Support Services, Other within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-business-managerial-economics-ms": {
        "summary": "Students and guides describe Kellogg's graduate offerings in in Business/Managerial Economics within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-chemical-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Chemical Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Chemical Engineering",
                "url": "https://www.mccormick.northwestern.edu/chemical-biological-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-chemical-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Chemical Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Chemical Engineering",
                "url": "https://www.mccormick.northwestern.edu/chemical-biological-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-civil-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Civil Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Civil Engineering",
                "url": "https://www.mccormick.northwestern.edu/civil-environmental-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-civil-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Civil Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Civil Engineering",
                "url": "https://www.mccormick.northwestern.edu/civil-environmental-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-communication-journalism-and-related-programs-other-bs": {
        "summary": "Students describe Medill's undergraduate program in Communication, Journalism, and Related Programs, Other as a practice-intensive journalism and media degree with Chicago newsroom access; praise includes the Knight Lab, Washington Program, and industry faculty, with cautions about limited graduate funding and portfolio-dependent career outcomes.",
        "themes": [
            {
                "label": "Practice-first training",
                "sentiment": "positive",
                "detail": "Reporting, multimedia, and IMC studios anchor the curriculum.",
            },
            {
                "label": "Chicago media market",
                "sentiment": "positive",
                "detail": "Internships at major newspapers, broadcasters, and agencies are strengths.",
            },
            {
                "label": "Knight Lab innovation",
                "sentiment": "positive",
                "detail": "Digital journalism resources differentiate Medill nationally.",
            },
            {
                "label": "Funding scarcity",
                "sentiment": "caution",
                "detail": "Graduate assistantships are scarcer than in STEM programs.",
            },
            {
                "label": "Portfolio careers",
                "sentiment": "mixed",
                "detail": "Outcomes depend on clips, internships, and industry networks.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Communication, Journalism, and Related Programs, Other",
                "url": "https://www.medill.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/national-universities",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-communication-journalism-and-related-programs-other-ms": {
        "summary": "Students describe Medill's graduate program in in Communication, Journalism, and Related Programs, Other as a practice-intensive journalism and media degree with Chicago newsroom access; praise includes the Knight Lab, Washington Program, and industry faculty, with cautions about limited graduate funding and portfolio-dependent career outcomes.",
        "themes": [
            {
                "label": "Practice-first training",
                "sentiment": "positive",
                "detail": "Reporting, multimedia, and IMC studios anchor the curriculum.",
            },
            {
                "label": "Chicago media market",
                "sentiment": "positive",
                "detail": "Internships at major newspapers, broadcasters, and agencies are strengths.",
            },
            {
                "label": "Knight Lab innovation",
                "sentiment": "positive",
                "detail": "Digital journalism resources differentiate Medill nationally.",
            },
            {
                "label": "Funding scarcity",
                "sentiment": "caution",
                "detail": "Graduate assistantships are scarcer than in STEM programs.",
            },
            {
                "label": "Portfolio careers",
                "sentiment": "mixed",
                "detail": "Outcomes depend on clips, internships, and industry networks.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Communication, Journalism, and Related Programs, Other",
                "url": "https://www.medill.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/national-universities",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-computer-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Computer Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Computer Engineering",
                "url": "https://www.mccormick.northwestern.edu/electrical-computer/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-computer-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Computer Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Computer Engineering",
                "url": "https://www.mccormick.northwestern.edu/electrical-computer/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-computer-science-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in Computer Science within McCormick as a research-oriented degree with strengths in AI, HCI, and systems through NICO and interdisciplinary CS+X ties; praise includes Chicago tech recruiting and faculty mentorship in a smaller cohort than CS-flagship giants, with cautions about self-funded tuition for terminal master's students and theory-heavy core requirements.",
        "themes": [
            {
                "label": "AI & HCI research",
                "sentiment": "positive",
                "detail": "NICO and CS labs connect computing to journalism, design, and social science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates place at major tech firms, startups, and Ph.D. programs nationally.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Smaller department enables closer advisor relationships than mega-departments.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Reviewers note fewer applied-software electives than some peer programs.",
            },
        ],
        "sources": [
            {
                "label": "McCormick \u2014 Computer Science Graduate",
                "url": "https://www.mccormick.northwestern.edu/computer-science/graduate/",
            },
            {
                "label": "U.S. News \u2014 Computer Science rankings",
                "url": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-data-science-bs": {
        "summary": "Students describe Northwestern's undergraduate program in Data Science within Weinberg as a liberal-arts degree at a top-10 national university \u2014 U.S. News ranks Northwestern #7 (2026); praise includes small seminars, faculty research access, and Chicago internships, with cautions that popular majors can have large introductory sections.",
        "themes": [
            {
                "label": "Top national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Northwestern #7 among national universities (2026).",
            },
            {
                "label": "Seminar culture",
                "sentiment": "positive",
                "detail": "Upper-level Weinberg courses emphasize discussion and faculty mentorship.",
            },
            {
                "label": "Chicago access",
                "sentiment": "positive",
                "detail": "Internships and research opportunities extend beyond the Evanston campus.",
            },
            {
                "label": "Large intro courses",
                "sentiment": "caution",
                "detail": "Popular majors can mean big lectures in gateway sequences.",
            },
            {
                "label": "Grad-school path",
                "sentiment": "mixed",
                "detail": "Many humanities and social-science majors pursue further graduate study.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Data Science",
                "url": "https://weinberg.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-economics-ms": {
        "summary": "Students and third-party guides describe Northwestern's graduate program in in Economics within Weinberg College of Arts and Sciences as a research-oriented degree at a top-10 national university; praise includes Northwestern's faculty and Chicago resources, with cautions about competitive admission, cost of living, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top-10 national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Northwestern #7 among national universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Economics lead research and professional training.",
            },
            {
                "label": "Chicago access",
                "sentiment": "positive",
                "detail": "Students leverage firms, hospitals, and cultural institutions in the Chicago area.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Northwestern graduate and professional programs have selective admission pools.",
            },
            {
                "label": "Cost & location",
                "sentiment": "caution",
                "detail": "Chicago-area living costs add to private-university tuition.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Economics",
                "url": "https://economics.weinberg.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-electrical-electronics-and-communications-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate program in Electrical, Electronics, and Communications Engineering within the School of Communication as a production- and research-oriented degree \u2014 U.S. News ranks Northwestern among leading fine-arts and communication programs; praise includes RTVF production training and Chicago media access, with cautions about limited funding and career variability in creative industries.",
        "themes": [
            {
                "label": "Production training",
                "sentiment": "positive",
                "detail": "Film, TV, and digital media production courses are program strengths.",
            },
            {
                "label": "Chicago media access",
                "sentiment": "positive",
                "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms.",
            },
            {
                "label": "Research integration",
                "sentiment": "positive",
                "detail": "Communication studies and performance research enrich production work.",
            },
            {
                "label": "Limited funding",
                "sentiment": "caution",
                "detail": "Graduate funding is scarcer than in STEM Ph.D. programs.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on portfolio quality and industry connections.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://www.mccormick.northwestern.edu/electrical-computer/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-electrical-electronics-and-communications-engineering-ms": {
        "summary": "Students describe Northwestern's graduate program in in Electrical, Electronics, and Communications Engineering within the School of Communication as a production- and research-oriented degree \u2014 U.S. News ranks Northwestern among leading fine-arts and communication programs; praise includes RTVF production training and Chicago media access, with cautions about limited funding and career variability in creative industries.",
        "themes": [
            {
                "label": "Production training",
                "sentiment": "positive",
                "detail": "Film, TV, and digital media production courses are program strengths.",
            },
            {
                "label": "Chicago media access",
                "sentiment": "positive",
                "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms.",
            },
            {
                "label": "Research integration",
                "sentiment": "positive",
                "detail": "Communication studies and performance research enrich production work.",
            },
            {
                "label": "Limited funding",
                "sentiment": "caution",
                "detail": "Graduate funding is scarcer than in STEM Ph.D. programs.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on portfolio quality and industry connections.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Electrical, Electronics, and Communications Engineering",
                "url": "https://www.mccormick.northwestern.edu/electrical-computer/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-engineering-related-technologies-technicians-other-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Engineering/Engineering-Related Technologies/Technicians, Other within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering/Engineering-Related Technologies/Technicians, Other",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-general-bs": {
        "summary": "Students describe Northwestern's undergraduate Engineering, General program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering, General",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-mechanics-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Engineering Mechanics within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering Mechanics",
                "url": "https://www.mccormick.northwestern.edu/mechanical-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-other-bs": {
        "summary": "Students describe Northwestern's undergraduate Engineering, Other program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering, Other",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-other-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Engineering, Other within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering, Other",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-physics-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Engineering Physics within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering Physics",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-related-fields-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Engineering-Related Fields within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering-Related Fields",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-engineering-science-bs": {
        "summary": "Students describe Northwestern's undergraduate Engineering Science program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Engineering Science",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-entrepreneurial-and-small-business-operations-bs": {
        "summary": "Students and guides describe Kellogg's undergraduate offerings in Entrepreneurial and Small Business Operations within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-entrepreneurial-and-small-business-operations-ms": {
        "summary": "Students and guides describe Kellogg's graduate offerings in in Entrepreneurial and Small Business Operations within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-environmental-environmental-health-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Environmental/Environmental Health Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Environmental/Environmental Health Engineering",
                "url": "https://www.mccormick.northwestern.edu/civil-environmental-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-film-video-and-photographic-arts-ms": {
        "summary": "Students describe Northwestern's graduate program in in Film/Video and Photographic Arts within the School of Communication as a production- and research-oriented degree \u2014 U.S. News ranks Northwestern among leading fine-arts and communication programs; praise includes RTVF production training and Chicago media access, with cautions about limited funding and career variability in creative industries.",
        "themes": [
            {
                "label": "Production training",
                "sentiment": "positive",
                "detail": "Film, TV, and digital media production courses are program strengths.",
            },
            {
                "label": "Chicago media access",
                "sentiment": "positive",
                "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms.",
            },
            {
                "label": "Research integration",
                "sentiment": "positive",
                "detail": "Communication studies and performance research enrich production work.",
            },
            {
                "label": "Limited funding",
                "sentiment": "caution",
                "detail": "Graduate funding is scarcer than in STEM Ph.D. programs.",
            },
            {
                "label": "Career variability",
                "sentiment": "mixed",
                "detail": "Outcomes depend on portfolio quality and industry connections.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Film/Video and Photographic Arts",
                "url": "https://communication.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-finance-and-financial-management-services-ms": {
        "summary": "Students and guides describe Kellogg's graduate offerings in in Finance and Financial Management Services within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-industrial-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Industrial Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Industrial Engineering",
                "url": "https://www.mccormick.northwestern.edu/industrial-engineering-management-sciences/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-industrial-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Industrial Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Industrial Engineering",
                "url": "https://www.mccormick.northwestern.edu/industrial-engineering-management-sciences/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-international-business-ms": {
        "summary": "Students and guides describe Kellogg's graduate offerings in in International Business within one of the nation's top MBA schools \u2014 Poets&Quants and U.S. News consistently rank Kellogg among leading business programs; praise includes collaborative culture and marketing strength, with cautions about selective admission, high tuition, and the fast-paced quarter system.",
        "themes": [
            {
                "label": "Collaborative culture",
                "sentiment": "positive",
                "detail": "Team-based learning is a Kellogg hallmark across programs.",
            },
            {
                "label": "Marketing strength",
                "sentiment": "positive",
                "detail": "Kellogg is perennially ranked among top marketing MBA programs.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg.",
            },
            {
                "label": "Quarter-system pace",
                "sentiment": "caution",
                "detail": "Ten-week quarters compress coursework and recruiting timelines.",
            },
            {
                "label": "Tuition cost",
                "sentiment": "caution",
                "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers.",
            },
        ],
        "sources": [
            {
                "label": "Kellogg School of Management",
                "url": "https://www.kellogg.northwestern.edu/",
            },
            {
                "label": "Poets&Quants \u2014 Kellogg",
                "url": "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-journalism-ms": {
        "summary": "Graduate students describe Medill's journalism master's as a practice-intensive program with Chicago newsroom access and integrated marketing communications tracks; praise includes the Knight Lab, Washington Program, and industry faculty, with cautions about limited graduate funding compared with STEM programs and career outcomes that depend heavily on portfolio and internship networks.",
        "themes": [
            {
                "label": "Practice-first training",
                "sentiment": "positive",
                "detail": "Reporting, multimedia, and IMC studios anchor the graduate curriculum.",
            },
            {
                "label": "Chicago media market",
                "sentiment": "positive",
                "detail": "Internships at major newspapers, broadcasters, and agencies are program strengths.",
            },
            {
                "label": "Knight Lab innovation",
                "sentiment": "positive",
                "detail": "Digital journalism and product innovation resources differentiate Medill.",
            },
            {
                "label": "Funding scarcity",
                "sentiment": "caution",
                "detail": "Graduate assistantships are scarcer than in STEM Ph.D. programs.",
            },
            {
                "label": "Portfolio-dependent careers",
                "sentiment": "mixed",
                "detail": "Outcomes hinge on clips, internships, and industry connections.",
            },
        ],
        "sources": [
            {
                "label": "Medill \u2014 Graduate Programs",
                "url": "https://www.medill.northwestern.edu/admission/graduate-programs/",
            },
            {
                "label": "Niche \u2014 Northwestern University",
                "url": "https://www.niche.com/colleges/northwestern-university/",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-law-phd": {
        "summary": "Doctoral scholars describe Northwestern Law's Law as a research degree within Pritzker School of Law \u2014 U.S. News ranks Northwestern Law among the nation's top programs \u2014 with praise for faculty mentorship and Chicago legal community access, with cautions about competitive academic hiring and limited funding relative to large public law schools.",
        "themes": [
            {
                "label": "Top law school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Northwestern Law among leading national programs.",
            },
            {
                "label": "Chicago legal market",
                "sentiment": "positive",
                "detail": "Proximity to major firms and courts supports research and clerkships.",
            },
            {
                "label": "Faculty mentorship",
                "sentiment": "positive",
                "detail": "Small doctoral cohorts enable close work with legal scholars.",
            },
            {
                "label": "Academic job market",
                "sentiment": "caution",
                "detail": "Tenure-track law faculty positions are nationally competitive.",
            },
            {
                "label": "Funding variability",
                "sentiment": "caution",
                "detail": "Doctoral funding packages vary; external fellowships are common.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Pritzker School of Law",
                "url": "https://www.law.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/northwestern-university-03058",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-manufacturing-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Manufacturing Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Manufacturing Engineering",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-manufacturing-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Manufacturing Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Manufacturing Engineering",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-materials-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Materials Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Materials Engineering",
                "url": "https://www.mccormick.northwestern.edu/materials-science-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-materials-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Materials Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Materials Engineering",
                "url": "https://www.mccormick.northwestern.edu/materials-science-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-mechanical-engineering-bs": {
        "summary": "Students describe Northwestern's undergraduate Mechanical Engineering program in McCormick as a quantitatively rigorous engineering degree with research-lab access and Chicago recruiting; praise includes NICO interdisciplinary ties and small upper-level classes, with cautions that core sequences are theory-heavy and demanding.",
        "themes": [
            {
                "label": "Engineering rigor",
                "sentiment": "positive",
                "detail": "McCormick's quantitative core prepares students for industry and grad school.",
            },
            {
                "label": "Research access",
                "sentiment": "positive",
                "detail": "Undergraduates join labs in bioengineering, CS, and materials science.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers.",
            },
            {
                "label": "Theory-heavy core",
                "sentiment": "mixed",
                "detail": "Strong mathematical foundations; some wish for more applied electives.",
            },
            {
                "label": "Workload",
                "sentiment": "caution",
                "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Mechanical Engineering",
                "url": "https://www.mccormick.northwestern.edu/mechanical-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-mechanical-engineering-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Mechanical Engineering within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Mechanical Engineering",
                "url": "https://www.mccormick.northwestern.edu/mechanical-engineering/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-mechanical-engineering-related-technologies-technicians-ms": {
        "summary": "Graduate applicants describe Northwestern's M.S. in in Mechanical Engineering Related Technologies/Technicians within McCormick as a research and coursework degree with interdisciplinary ties to Feinberg, Medill, and NICO; students value Chicago industry recruiting and faculty labs, with cautions about self-funded tuition for terminal master's students and competitive funding.",
        "themes": [
            {
                "label": "Engineering reputation",
                "sentiment": "positive",
                "detail": "McCormick is consistently ranked among leading engineering schools.",
            },
            {
                "label": "Interdisciplinary research",
                "sentiment": "positive",
                "detail": "NICO, bioelectronics, and med-tech partnerships span schools.",
            },
            {
                "label": "Chicago recruiting",
                "sentiment": "positive",
                "detail": "Graduates enter industry R&D, consulting, and doctoral programs.",
            },
            {
                "label": "Self-funded MS",
                "sentiment": "caution",
                "detail": "Terminal master's students without assistantships typically self-fund tuition.",
            },
            {
                "label": "Funding competition",
                "sentiment": "caution",
                "detail": "Research assistantships are competitive across McCormick.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Mechanical Engineering Related Technologies/Technicians",
                "url": "https://www.mccormick.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-medicine-phd": {
        "summary": "Graduate students describe Feinberg's doctoral program in Medicine as a research-intensive health-sciences degree with access to Northwestern Memorial Hospital and Shirley Ryan AbilityLab \u2014 U.S. News ranks Feinberg among top research medical schools; praise includes translational research infrastructure, with cautions about competitive residency matching and Chicago living costs.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Feinberg among leading medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Northwestern Memorial and affiliated sites support clinical research.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students join labs spanning basic science and clinical trials.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Chicago housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Feinberg School of Medicine",
                "url": "https://www.feinberg.northwestern.edu/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-04094",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-public-health-bs": {
        "summary": "Students and third-party guides describe Northwestern's undergraduate program in Public Health within Feinberg School of Medicine as a professionally focused degree at a top-10 national university; praise includes Northwestern's faculty and Chicago resources, with cautions about competitive admission, cost of living, and career outcomes that vary by field.",
        "themes": [
            {
                "label": "Top-10 national rank",
                "sentiment": "positive",
                "detail": "U.S. News ranks Northwestern #7 among national universities (2026).",
            },
            {
                "label": "Faculty expertise",
                "sentiment": "positive",
                "detail": "Faculty in Public Health lead research and professional training.",
            },
            {
                "label": "Chicago access",
                "sentiment": "positive",
                "detail": "Students leverage firms, hospitals, and cultural institutions in the Chicago area.",
            },
            {
                "label": "Competitive admission",
                "sentiment": "caution",
                "detail": "Northwestern graduate and professional programs have selective admission pools.",
            },
            {
                "label": "Cost & location",
                "sentiment": "caution",
                "detail": "Chicago-area living costs add to private-university tuition.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Public Health",
                "url": "https://www.feinberg.northwestern.edu/sites/health-sciences/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-04094",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
    "northwestern-public-health-ms": {
        "summary": "Graduate students describe Feinberg's graduate program in in Public Health as a research-intensive health-sciences degree with access to Northwestern Memorial Hospital and Shirley Ryan AbilityLab \u2014 U.S. News ranks Feinberg among top research medical schools; praise includes translational research infrastructure, with cautions about competitive residency matching and Chicago living costs.",
        "themes": [
            {
                "label": "Top research medical school",
                "sentiment": "positive",
                "detail": "U.S. News ranks Feinberg among leading medical schools for research.",
            },
            {
                "label": "Hospital access",
                "sentiment": "positive",
                "detail": "Northwestern Memorial and affiliated sites support clinical research.",
            },
            {
                "label": "Translational research",
                "sentiment": "positive",
                "detail": "Students join labs spanning basic science and clinical trials.",
            },
            {
                "label": "Residency competition",
                "sentiment": "caution",
                "detail": "Competitive specialties require strong boards and research portfolios.",
            },
            {
                "label": "Living costs",
                "sentiment": "caution",
                "detail": "Chicago housing adds to professional-school tuition.",
            },
        ],
        "sources": [
            {
                "label": "Northwestern \u2014 Public Health",
                "url": "https://www.feinberg.northwestern.edu/sites/health-sciences/",
            },
            {
                "label": "U.S. News \u2014 Northwestern University",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-04094",
            },
        ],
        "disclaimer": _DISCLAIMER,
    },
}
